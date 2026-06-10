.PHONY: install test bump

install:
	pip install -r requirements.txt

test:
	pytest -q

# Usage: make bump VERSION=2.9.0
bump:
	@test -n "$(VERSION)" || (echo "Usage: make bump VERSION=x.y.z" && exit 1)
	@sed -i '' 's/"version": "[^"]*"/"version": "$(VERSION)"/' .claude-plugin/plugin.json
	@sed -i '' 's/"version": "[^"]*"/"version": "$(VERSION)"/' .claude-plugin/marketplace.json
	@sed -i '' 's/"version": "[^"]*"/"version": "$(VERSION)"/' INSTALL.md
	@echo "Bumped to $(VERSION) in plugin.json, marketplace.json, INSTALL.md"
	@echo "Add a ## [$(VERSION)] — $$(date +%Y-%m-%d) entry to CHANGELOG.md, then commit."
