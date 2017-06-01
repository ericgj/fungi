
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

- Make python3 compatible. 


## Enhancements

- Deal with necessary "response mutation" in a broader way. Besides setting
  cookies, there are mutable operations to unset/delete/merge cookies; gzip-ing 
  contents; setting etag based on hash of contents. I don't see other operations
  in webob, but I may be missing others.

    type ResponseOp
      = NoOp
      | SetCookie Cookie
      | DeleteCookie String String (Maybe String)  -- name, path, domain
      | UnsetCookie String  -- name
      | GzipEncode
      | SetETag
      | Batch ResponseOp

  Note no `MergeCookie` -- that's if you have two responses for some reason.
  That would never happen here. And I don't think we actually need Delete or
  Unset either.

  I think the current 'response adapter' way of fudging the types based on 
  whether receiving a single value or a tuple, is perfectly 'pythonic', ie.
  a potential source of pain down the road :) 

  Instead I propose a wrapper you could use to pass through ResponseOp in a 
  tuple:

      my_handler(req) >> finalize_response_after( encode_json )

      @curry
      def finalize_response_after(fn, (a, op)):
        # ( a -> Task Exception (Dict, ResponseOp) ) -> 
        # (a, ResponseOp) -> 
        # Task Exception (Dict, ResponseOp)
        return (
          fn(a).fmap(
            lambda (newstate, newop): ( newstate, mconcat(op, newop) ) 
          )
        )

  This would work assuming the adapters are now all
  `( a -> Task Exception (Dict, ResponseOp) )` -- returning NoOp in the second
  tuple element typically. You could also have:

      gzip_encode_json = encode_json.fmap( and_finalize(GzipEncode) )

      def and_finalize(newop, (a,op)):
        return (a, mconcat(op,newop))
  

- Some helpers for a more 'declarative' way of constructing API endpoints. I 
  am inspired by python [graphql-core][], which lets you specify the response
  tree with 'resolvers' on the leaves. These are collected, executed, and
  the response tree built up with them. And it even abstracts the execution 
  model, so you can run them concurrently under various concurrency schemes.


[oauthlib]: https://oauthlib.readthedocs.io/en/latest/
[requests-oauthlib]: http://requests-oauthlib.readthedocs.io/en/latest/
[graphql-core]: https://github.com/graphql-python/graphql-core

