#!/usr/bin/env python3
"""
scripts/publish_dataset.py

Uploads pre-packaged Synthlore benchmark distributions to Hugging Face Datasets
or Kaggle Datasets via official APIs.

Usage:
  # Hugging Face:
  python scripts/publish_dataset.py --target huggingface --repo_id <username>/synthlore-benchmark [--token <token>]

  # Kaggle:
  python scripts/publish_dataset.py --target kaggle [--username <user>] [--key <key>]
"""

import os
import sys
import argparse
from pathlib import Path


def upload_huggingface(repo_id: str, token: str = None):
    try:
        from huggingface_hub import HfApi, create_repo
    except ImportError:
        print("Error: huggingface_hub is not installed. Install via:")
        print("  pip install huggingface_hub")
        sys.exit(1)

    token = token or os.environ.get("HF_TOKEN")
    if not token:
        print("Error: No Hugging Face token provided.")
        print("Pass --token or set the HF_TOKEN environment variable.")
        print("Get your token at: https://huggingface.co/settings/tokens (with write permission)")
        sys.exit(1)

    root = Path(__file__).resolve().parent.parent
    hf_dist = root / "dist" / "huggingface"
    if not hf_dist.exists():
        print("Error: dist/huggingface does not exist. Run scripts/prepare_dataset_distribution.py first.")
        sys.exit(1)

    api = HfApi(token=token)
    print(f"Creating / verifying dataset repository: {repo_id}...")
    create_repo(repo_id=repo_id, repo_type="dataset", token=token, exist_ok=True)

    print(f"Uploading files from {hf_dist} to {repo_id}...")
    api.upload_folder(
        folder_path=str(hf_dist),
        repo_id=repo_id,
        repo_type="dataset",
        commit_message="Initial release of Synthlore RAG benchmark corpus and evaluation splits"
    )
    print(f"\nSuccessfully published to Hugging Face!")
    print(f"View dataset: https://huggingface.co/datasets/{repo_id}")


def upload_kaggle(username: str = None, key: str = None):
    try:
        import kaggle
    except ImportError:
        print("Error: kaggle package is not installed. Install via:")
        print("  pip install kaggle")
        sys.exit(1)

    if username:
        os.environ["KAGGLE_USERNAME"] = username
    if key:
        os.environ["KAGGLE_KEY"] = key

    root = Path(__file__).resolve().parent.parent
    kaggle_dist = root / "dist" / "kaggle"
    if not kaggle_dist.exists():
        print("Error: dist/kaggle does not exist. Run scripts/prepare_dataset_distribution.py first.")
        sys.exit(1)

    meta_path = kaggle_dist / "dataset-metadata.json"
    if not meta_path.exists():
        print("Error: dataset-metadata.json not found in dist/kaggle.")
        sys.exit(1)

    print("Authenticating with Kaggle API...")
    from kaggle.api.kaggle_api_extended import KaggleApi
    api = KaggleApi()
    api.authenticate()

    print(f"Creating / updating dataset on Kaggle from {kaggle_dist}...")
    try:
        api.dataset_create_new(folder=str(kaggle_dist), public=True, quiet=False)
        print("\nSuccessfully published new dataset to Kaggle!")
    except Exception as e:
        print(f"Create failed ({e}), attempting version update...")
        api.dataset_create_version(folder=str(kaggle_dist), version_notes="Initial release", quiet=False)
        print("\nSuccessfully updated dataset version on Kaggle!")


def main():
    parser = argparse.ArgumentParser(description="Publish Synthlore dataset to Hugging Face or Kaggle.")
    parser.add_argument("--target", choices=["huggingface", "kaggle"], required=True, help="Target platform")
    parser.add_argument("--repo_id", help="Hugging Face repo id (e.g. username/synthlore-benchmark)")
    parser.add_argument("--token", help="Hugging Face API token")
    parser.add_argument("--username", help="Kaggle username")
    parser.add_argument("--key", help="Kaggle API key")

    args = parser.parse_args()

    if args.target == "huggingface":
        if not args.repo_id:
            print("Error: --repo_id is required for huggingface (e.g. --repo_id NavinYP/synthlore-benchmark)")
            sys.exit(1)
        upload_huggingface(repo_id=args.repo_id, token=args.token)
    elif args.target == "kaggle":
        upload_kaggle(username=args.username, key=args.key)


if __name__ == "__main__":
    main()
