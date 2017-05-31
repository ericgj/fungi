
# TODO

## Maintenance

- Documentation and examples

- The oauth2client library is deprecated as of May 2017. We need to sort out 
  replacing three bits:
    - client.OAuth2WebServerFlow  (.step1_get_authorize_url)
    - client.Credentials  (.authorize, .access_token_expired)
    - contrib.xsrfutil

  Note the GAE-specific NDB model is inlined, so really there is no reason to 
  rely on a Google-provided library. It seems like [oauthlib][] in combination
  with an http library would do the trick, e.g. [requests-oauthlib][] but 
  without the horrid mutable state and hiding side effects :)  The XSRF stuff
  could be inlined/taken from somewhere else.


## Enhancements

- Some helpers for a more 'declarative' way of constructing API endpoints. I 
  am inspired by python [graphql-core][], which lets you specify the response
  tree with 'resolvers' on the leaves. These are collected, executed, and
  the response tree built up with them. And it even abstracts the execution 
  model, so you can run them concurrently under various concurrency schemes.


[oauthlib]: https://oauthlib.readthedocs.io/en/latest/
[requests-oauthlib]: http://requests-oauthlib.readthedocs.io/en/latest/


