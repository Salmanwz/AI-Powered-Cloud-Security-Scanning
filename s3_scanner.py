import boto3
import os, json
import logging
import google.generativeai as genai

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)   

def lambda_handler(event, context):
    """Scan S3 buckets for encryption and use AI to explain risks

    Args:
        event (_type_): _description_
        context (_type_): _description_

    Returns:
        json: Scan results and AI analysis
    """
    # Initialize AWS S3 client
    s3_client = boto3.client('s3')
    logger.info("Scanning S3 buckets for encryption status.")

    # List all S3 buckets
    buckets = s3_client.list_buckets().get('Buckets', [])
    logger.info(f"Found {len(buckets)} buckets.")

    # Store results
    results = []

    for bucket in buckets:
        bucket_name = bucket['Name']

        # Check bucket encryption status
        try:
            encryption = s3_client.get_bucket_encryption(Bucket=bucket_name)
            encryption_status = "Enabled"
            encryption_status_details = encryption['ServerSideEncryptionConfiguration']
        except s3_client.exceptions.ClientError as e:
            if e.response['Error']['Code'] == 'ServerSideEncryptionConfigurationNotFoundError':
                encryption_status = "Not Enabled"
                encryption_status_details = None
            else:
                logger.error(f"Error checking encryption for bucket {bucket_name}: {e}")
                continue

        # Store results
        results.append({
            "bucket_name": bucket_name,
            "encryption_status": encryption_status,
            "encryption_status_details": encryption_status_details
        })
        logger.info(f"Bucket: {bucket_name}, Encryption Status: {encryption_status}")


    # Count unencrypted buckets

    unencrypted_buckets = [b for b in results if b['encryption_status'] == "Not Enabled"]
    unencrypted_count = len(unencrypted_buckets)
    logger.info(f"Total unencrypted buckets: {unencrypted_count}")

    
    # Use Google Generative AI to explain risks
    api_key = os.environ.get('GOOGLE_API_KEY')
    if not api_key:
        ai_analysis = "AI analysis skipped: GOOGLE_API_KEY not configured"
    else:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.0-flash-exp")

        prompt = f"""You are an AWS security expert. Analyze this S3 encryption scan and provide a brief security assessment.

                    Scan Results:

                    - Total Buckets: {len(buckets)}
                    - Encrypted: {len(buckets) - unencrypted_count}
                    - Unencrypted: {unencrypted_count}
                    - Unencrypted Bucket Names: {', '.join(unencrypted_buckets) if unencrypted_buckets else 'None'}

                    Provide a 2-3 sentence analysis:
                    1. What's the security risk of unencrypted buckets?
                    2. What encryption should be enabled? (AES256 or aws:kms)
                    3. What action should the user take immediately?

                    Be concise and actionable.
                """

        try:
            response = model.generate_content(prompt)
            ai_analysis = response.text
        except Exception as e:
            ai_analysis = f"AI analysis failed: {str(e)}"
            logger.error(f"Error during AI analysis: {e}")

    # Build final result
    result = {
        'total_buckets': len(buckets),
        'unencrypted_buckets': unencrypted_count,
        'encrypted_buckets': len(buckets) - unencrypted_count,
        'scan_results': results,
        'ai_analysis': ai_analysis,
        'alert': unencrypted_count > 0
    }

    logger.info(f"\nScan complete: {unencrypted_count}/{len(buckets)} buckets need encryption")

    return {
        'statusCode': 200,
        'body': json.dumps(result)
    }



