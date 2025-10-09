
build: components index.js
	@component build --dev

components: component.json
	@component install --dev

clean:
	rm -fr build components template.js

test: node_modules
	@./node_modules/mocha/bin/mocha \
		--reporter spec

node_modules: package.json
	@npm install

.PHONY: clean
