#%%
import pandas as pd
import requests
import base64
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient


# --- CONFIGURATION ---
KEY_VAULT_NAME = "kv-azure-data-techs"  # Replace with your actual Key Vault name
SECRET_NAME = "DevOps-PAT"     # Replace with your secret name
VAULT_URL = f"https://kv-azure-data-techs.vault.azure.net/"

ORGANIZATION = "linkedlauren"     # e.g., mydevopsorg
PROJECT = "Wood Valley Analytics - Valor Venue"      # e.g., InventoryApp
EXCEL_FILE = "inventory_project_work_items.xlsx"
API_VERSION = "7.1-preview.3"

# --- AUTHENTICATION ---
credential = DefaultAzureCredential()
secret_client = SecretClient(vault_url=VAULT_URL, credential=credential)
pat = secret_client.get_secret(SECRET_NAME).value

# Encode PAT for Basic Auth
auth_header = str(base64.b64encode(bytes(':' + pat, 'ascii')), 'ascii')
headers = {
    'Content-Type': 'application/json-patch+json',
    'Authorization': f'Basic {auth_header}'
}

# --- LOAD EXCEL FILE ---
df = pd.read_excel(EXCEL_FILE)

# --- CREATE WORK ITEMS ---
base_url = f"https://dev.azure.com/{ORGANIZATION}/{PROJECT}/_apis/wit/workitems"
work_item_ids = {}  # Maps Title to ID for parent linking

for _, row in df.iterrows():
    item_type = row["Work Item Type"]
    title = row["Title"]
    parent_title = row["Parent"] if pd.notnull(row["Parent"]) else None

    # Create the work item
    body = [
        {"op": "add", "path": "/fields/System.Title", "value": title}
    ]

    response = requests.post(
        f"{base_url}/${item_type}?api-version={API_VERSION}",
        headers=headers,
        json=body
    )

    if response.status_code in (200, 201):
        item_id = response.json()["id"]
        work_item_ids[title] = item_id
        print(f"✅ Created {item_type}: {title} (ID: {item_id})")

        # Link to parent if applicable
        if parent_title and parent_title in work_item_ids:
            parent_id = work_item_ids[parent_title]
            link_body = [
                {
                    "op": "add",
                    "path": "/relations/-",
                    "value": {
                        "rel": "System.LinkTypes.Hierarchy-Reverse",
                        "url": f"https://dev.azure.com/{ORGANIZATION}/_apis/wit/workItems/{parent_id}",
                        "attributes": {"comment": "Linked to parent"}
                    }
                }
            ]
            patch_response = requests.patch(
                f"{base_url}/{item_id}?api-version={API_VERSION}",
                headers=headers,
                json=link_body
            )
            if patch_response.status_code in (200, 204):
                print(f"🔗 Linked {title} to parent {parent_title}")
            else:
                print(f"⚠️ Failed to link {title} to parent: {patch_response.text}")
    else:
        print(f"❌ Failed to create {item_type}: {title}")
        print(response.text)

# %%
