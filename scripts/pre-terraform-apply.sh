#!/bin/bash
# Pre-terraform apply hook: Build and push Docker image before terraform apply

# Check if command contains "terraform apply"
if echo "$CLAUDE_TOOL_INPUT" | grep -q "terraform apply"; then
    echo "Detected terraform apply - building Docker image first..."

    cd /Users/gaku/project/job-recommender

    # Build and push Docker image
    gcloud builds submit \
        --tag asia-northeast1-docker.pkg.dev/job-recommender-483205/job-recommender/app:latest \
        --quiet

    if [ $? -eq 0 ]; then
        echo "Docker image built and pushed successfully"
    else
        echo "Failed to build Docker image"
        exit 1
    fi
fi
