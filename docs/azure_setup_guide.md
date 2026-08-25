# Azure OpenAI Setup Guide (2026 Edition)

As of 2026, Microsoft has streamlined the deployment of AI models by consolidating the experience into **Azure AI Foundry** (formerly Azure AI Studio). This is the recommended approach for setting up endpoints and keys for our pipeline.

Follow these steps to configure your environment for **Phase 2 (Text Compilation)**.

## Step 1: Create an Azure AI Foundry Resource
1. Sign in to the [Azure Portal](https://portal.azure.com).
2. Ensure you have an active Azure subscription with sufficient permissions (Contributor or Owner) and that your account has been approved for Azure OpenAI access.
3. In the search bar, type **Azure AI Foundry** or **Azure OpenAI** and select it from the Marketplace.
4. Click **Create** and configure the resource:
   * **Subscription & Resource Group:** Select your active subscription and create a new resource group (e.g., `rg-synthlore`).
   * **Region:** Choose a region that supports the models you need (e.g., `East US` or `Sweden Central` for extensive GPT-4o availability).
   * **Name:** Provide a unique name (e.g., `synthlore-ai-hub`).
   * **Pricing Tier:** Select **Standard**.
5. Click **Review + Create** and wait for the deployment to finish.

## Step 2: Deploy a Model
Once the Foundry resource is deployed, you need to instantiate a specific model.
1. Navigate to your newly created resource and click to open the **Azure AI Foundry Studio**.
2. On the left-hand navigation menu, look under the **Management** section and select **Deployments**.
3. Click **Create new deployment**.
4. Configure your deployment:
   * **Model:** Select `gpt-4o` (or `gpt-4o-mini` for cost-efficiency during testing).
   * **Model Version:** Select the latest default version.
   * **Deployment Name:** Name this deployment (e.g., `gpt-4o-synthlore`). **Note:** This exact string will be required in your `.env` configuration file later.
   * **Deployment Type:** Choose **Standard** (Pay-As-You-Go).
5. Click **Create**.

## Step 3: Retrieve API Keys and Endpoint
To connect our Python Langchain pipeline to your new model:
1. In the Azure AI Foundry Studio (or back in the Azure Portal for your resource), navigate to the **Keys and Endpoint** section.
2. Copy the following values:
   * **KEY 1** (This is your API Key)
   * **Endpoint** (Usually looks like `https://<your-resource-name>.openai.azure.com/`)

## Step 4: Local Environment Configuration
Create a `.env` file in the root of the `synthlore` project repository and populate it with the values you just retrieved:

```env
AZURE_OPENAI_API_KEY="your-key-1-here"
AZURE_OPENAI_ENDPOINT="https://your-resource-name.openai.azure.com/"
AZURE_OPENAI_API_VERSION="2026-04-01-preview" # Use the latest API version supported by Langchain
AZURE_OPENAI_DEPLOYMENT_NAME="gpt-4o-synthlore"
```

## Security Note for Scale
If we transition to generating the full 2,000-page corpus, consider configuring **Provisioned Throughput Units (PTUs)** in the Foundry Studio to guarantee reserved capacity and avoid rate-limiting interruptions.
