
### Login

When you control a Firefox Account (by proving you know the password), you get the ability to create BrowserID-like signed assertions. To be specific, you can submit a public key, and the server will give you back a signed certificate which tells the world that your keypair speaks for a particular FxA account id (which looks like "GUID@api.accounts.firefox.com"). You can then use your private key to create assertions for difference audience RPs, and submit the certificate+assertion pair as a bearer token to those RPs. This works a lot like Persona, except that the "principal" is an FxA account ID, not an email address.
