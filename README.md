# AI-Powered AWS S3 Security Scanner

An automated security monitoring solution that scans AWS S3 buckets for encryption compliance and provides AI-generated security recommendations using Google's Gemini API. All AWS infrastructure is deployed using Terraform (Infrastructure as Code).

## 🏗️ Architecture

![Architecture Diagram](/img/Project%20Diagrams%20-%20AI%20CSPM%20using%20AI.png)

**Workflow:**
- EventBridge triggers Lambda every 12 hours
- Lambda scans all S3 buckets for encryption status
- Gemini AI analyzes findings and generates recommendations
- Results are pushed to Cloud Watch

## ✨ Features

- **Automated S3 Scanning**: Checks all S3 buckets for encryption configuration
- **AI-Powered Analysis**: Uses Gemini AI to transform raw findings into actionable security recommendations
- **Scheduled Monitoring**: Runs automatically every 12 hours via EventBridge
- **Infrastructure as Code**: Complete Terraform deployment for reproducible infrastructure
- **Comprehensive Logging**: Full execution logs in CloudWatch for audit trails

## 🔧 Prerequisites

- AWS Account with appropriate permissions
- [AWS CLI](https://aws.amazon.com/cli/) configured with credentials
- [Terraform](https://www.terraform.io/downloads) (v1.0+)
- Python 3.12+
- Google AI Studio API key

## 📦 Project Structure

```
aws-monitor-gemini/
├── s3_scanner.py           # Lambda function code
├── requirements.txt        # Python dependencies
├── img/                    # Images and diagrams
│   └── Project Diagrams - AI CSPM using AI.png
├── infra/              # Terraform configuration files
|   ├── terraform.tf 
│   ├── main.tf
│   ├── variables.tf
│   └── terraform.tfvars
├── .gitignore
└── README.md
```

## 🚀 Getting Started

### Step 1: Get Gemini API Key

1. Navigate to [Google AI Studio](https://aistudio.google.com/)
2. Click **Get API key** in the left sidebar
3. Click **Create API key**
4. Create a new project (e.g., "AWS S3 Security Scanner")
5. Copy and securely save your API key

### Step 2: Setup Project Directory

```bash
# Create and navigate to project directory
git clone https://github.com/Salmanwz/AI-Powered-Cloud-Security-Scanning.git
cd AI-Powered-Cloud-Security-Scanning.git
```


### Step 3: Package Lambda Function

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Create package directory and install dependencies
mkdir package
pip install --platform manylinux2014_x86_64 \
    --target ./package \
    --implementation cp \
    --python-version 3.12 \
    --only-binary=:all: \
    -r requirements.txt

# Package Lambda function
cp s3_scanner.py package/
cd package && zip -r ../s3_scanner.zip . && cd ..
```

**Windows PowerShell Alternative:**
```powershell
python -m venv venv
venv\Scripts\activate
mkdir package
pip install --platform manylinux2014_x86_64 --target ./package --implementation cp --python-version 3.12 --only-binary=:all: -r requirements.txt
Copy-Item s3_scanner.py package/
Compress-Archive -Path package\* -DestinationPath s3_scanner.zip -Force
```

### Step 4: Configure Terraform

Create your Terraform configuration files in the `terraform/` directory:
- **`terraform.tf**: Setup you terraform provider.
- **`main.tf`**: Define IAM roles and policies, Lambda function, EventBridge rule, CloudWatch log
- **`variables.tf`**: Define input variables (region, function name, API key, schedule).

Create `infra/terraform.tfvars`:

```hcl
google_api_key       = "your-gemini-api-key-here"
```

⚠️ **Security**: Add `terraform.tfvars` to `.gitignore` to protect sensitive data!

### Step 5: Deploy Infrastructure with Terraform

```bash
cd terraform

# Initialize Terraform
terraform init

# Review execution plan
terraform plan

# Deploy infrastructure
terraform apply
```

Type `yes` when prompted to confirm deployment.

### Step 6: Verify Deployment

**Test Lambda Function:**
```bash
# Invoke Lambda function manually
aws lambda invoke \
    --function-name s3-security-scanner \
    --payload '{"test":"manual-invoke"}' \
    response.json

# View response
cat response.json
```

**View CloudWatch Logs:**
```bash
# Get latest log stream
aws logs describe-log-streams \
    --log-group-name /aws/lambda/s3-security-scanner \
    --order-by LastEventTime \
    --descending \
    --max-items 1

# View logs (replace LOG_STREAM_NAME with actual value)
aws logs get-log-events \
    --log-group-name /aws/lambda/s3-security-scanner \
    --log-stream-name LOG_STREAM_NAME
```

## 📊 Monitoring

The scanner runs automatically every 12 hours via EventBridge. View results in:

- **CloudWatch Logs**: `/aws/lambda/s3-security-scanner`
- **CloudWatch Metrics**: Lambda invocations, errors, duration


## 🔒 Security Best Practices

- Store API keys in Terraform variables, not in code
- Use `.gitignore` to exclude `terraform.tfvars` and `*.zip` files
- Apply least privilege IAM permissions
- Enable CloudWatch Logs encryption (add to Terraform config)
- Regularly rotate API keys
- Review CloudWatch logs for anomalies

## 🐛 Troubleshooting

**Lambda timeout errors:**
- Increase `lambda_timeout` in `terraform.tfvars`
- Check CloudWatch Logs for specific errors

**API key not working:**
- Verify `GOOGLE_API_KEY` environment variable is set in Lambda
- Check API key hasn't expired or been revoked

**Permission errors:**
- Verify IAM role has required S3 permissions
- Check Lambda execution role is properly attached

## 📚 Resources

- [AWS Lambda Documentation](https://docs.aws.amazon.com/lambda/)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [Google Gemini API Documentation](https://ai.google.dev/docs)
- [AWS EventBridge Documentation](https://docs.aws.amazon.com/eventbridge/)

---
