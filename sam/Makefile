.PHONY: build deploy clean

# Generate requirements.txt from uv lock file and build SAM application
build:
	cd .. && uv export --no-dev --no-emit-project --no-hashes > requirements.txt
	sam build

# Deploy to AWS (requires AWS credentials and environment variables)
# Required env vars: WILMA_EMAIL, WILMA_PASSWORD, ANTHROPIC_API_KEY, 
#                    TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, WILMA_DIGEST_CMD
deploy: build
	sam deploy --parameter-overrides \
		"WilmaEmail=$(WILMA_EMAIL)" \
		"WilmaPassword=$(WILMA_PASSWORD)" \
		"AnthropicApiKey=$(ANTHROPIC_API_KEY)" \
		"TelegramBotToken=$(TELEGRAM_BOT_TOKEN)" \
		"TelegramChatId=$(TELEGRAM_CHAT_ID)" \
		"WilmaDigestCmd=$(WILMA_DIGEST_CMD)"

# Clean build artifacts
clean:
	rm -rf .aws-sam
	rm -f ../requirements.txt
