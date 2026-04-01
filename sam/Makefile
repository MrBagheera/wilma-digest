.PHONY: build deploy clean

# Generate requirements.txt from uv lock file and build SAM application
build:
	cd .. && uv export --no-dev --no-emit-project --no-hashes > requirements.txt
	sam build

# Deploy to AWS (requires AWS credentials)
deploy: build
	sam deploy

# Clean build artifacts
clean:
	rm -rf .aws-sam
	rm -f ../requirements.txt
