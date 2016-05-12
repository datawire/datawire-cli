`/health`
- GET

`/v1/orgs`
- GET -- list of orgs (requires supertoken)
- POST -- create a new org (requires no token at all)
   - orgName
   - adminName
   - adminEmail
   - adminPassword
   - scopes (optional)

`/v1/orgs/:orgID`
- GET -- presently 403 (should be 404)

`/v1/users/:orgID`
- **GET -- list of users (requires org admin token)
- POST -- generates an invite
   - email
   - scopes (optional)

`/v1/users/:orgID/:email`
- GET -- presently 403 (should be 404)
- **DELETE -- deactivate a user (and revoke their tokens?) (requires org admin token)
- PUT -- update user record (including turning invite into a real user)

`/v1/auth`
- POST -- authenticate a user
   - email
   - password
   - orgID

`/v1/auth/:email`
- POST -- authenticate a user
   - password
   - orgID

`/v1/services/:orgID`
- POST -- create a new service

`** was /v1/svcCheck/:orgID/:svcHandle`
`** becomes /v1/services/:handle`
- GET -- check bearer token
