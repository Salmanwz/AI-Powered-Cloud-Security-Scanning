import boto3
import os, json
import logging
import google.generativeai as genai
import urllib3

# Configure logging for CloudWatch
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize HTTP client for Discord webhook
http = urllib3.PoolManager()

def send_to_discord(webhook_url, result):
    """Send scan results to Discord webhook with formatted embed
    
    Args:
        webhook_url (str): Discord webhook URL
        result (dict): Scan results to send
    """
    try:
        # Determine embed color based on findings
        if result['unencrypted_buckets'] > 0:
            color = 15158332  # Red
            status_emoji = "🚨"
            title = "S3 Security Scan - Action Required"
        else:
            color = 3066993  # Green

            title = "S3 Security Scan - All Clear"
        
        # Build unencrypted bucket list
        unencrypted_list = [b['bucket_name'] for b in result['scan_results'] 
                           if b['encryption_status'] == "Not Enabled"]
        
        # Create embed fields
        fields = [
            {
                "name": "📊 Summary",
                "value": f"**Total Buckets:** {result['total_buckets']}\n"
                        f"**Encrypted:** {result['encrypted_buckets']} ✅\n"
                        f"**Unencrypted:** {result['unencrypted_buckets']} ⚠️",
                "inline": False
            }
        ]
        
        # Add unencrypted buckets if any
        if unencrypted_list:
            bucket_list = '\n'.join([f"• `{b}`" for b in unencrypted_list[:10]])  # Limit to 10
            if len(unencrypted_list) > 10:
                bucket_list += f"\n• ... and {len(unencrypted_list) - 10} more"
            
            fields.append({
                "name": "⚠️ Unencrypted Buckets",
                "value": bucket_list,
                "inline": False
            })
        
        # Add AI analysis
        if result['ai_analysis'] and not result['ai_analysis'].startswith("AI analysis"):
            fields.append({
                "name": "🤖 AI Security Analysis",
                "value": result['ai_analysis'][:1024],  # Discord field limit
                "inline": False
            })
        
        # Create Discord message
        message = {
            "embeds": [{
                "title": f"{status_emoji} {title}",
                "color": color,
                "fields": fields,
                "footer": {
                    "text": "AWS S3 Security Scanner • Powered by Lambda + Gemini AI"
                },
                "timestamp": None  # Discord will use current time
            }]
        }
        
        # Send to Discord
        encoded_data = json.dumps(message).encode('utf-8')
        response = http.request(
            'POST',
            webhook_url,
            body=encoded_data,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status == 204:
            logger.info("Successfully sent results to Discord")
        else:
            logger.warning(f"Discord webhook returned status {response.status}")
            
    except Exception as e:
        logger.error(f"Failed to send to Discord: {e}")

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
        model = genai.GenerativeModel("gemini-2.5-flash-lite")

        # Fix: Extract bucket names properly
        unencrypted_bucket_names = [b['bucket_name'] for b in unencrypted_buckets]

        prompt = f"""You are an AWS security expert. Analyze this S3 encryption scan and provide a brief security assessment.

                    Scan Results:

                    - Total Buckets: {len(buckets)}
                    - Encrypted: {len(buckets) - unencrypted_count}
                    - Unencrypted: {unencrypted_count}
                    - Unencrypted Bucket Names: {', '.join(unencrypted_bucket_names) if unencrypted_bucket_names else 'None'}

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

    # Send results to Discord
    webhook_url = os.environ.get('DISCORD_WEBHOOK_URL')
    if webhook_url:
        send_to_discord(webhook_url, result)
    else:
        logger.warning("DISCORD_WEBHOOK_URL not configured, skipping Discord notification")

    return {
        'statusCode': 200,
        'body': json.dumps(result)
    }