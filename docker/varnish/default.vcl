vcl 4.1;

backend default {
    .host = "127.0.0.1";
    .port = "5000";
}

sub vcl_recv {
    set req.http.X-Forwarded-For = client.ip;
    
    if (req.url ~ "\.(js|css)(\?.*)?$") {
        return (hash);
    }
    
    return (pass);
}

sub vcl_hash {
    if (req.url ~ "\.(js|css)(\?.*)?$") {
        hash_data(req.url);
        if (req.http.accept) {
            hash_data(req.http.accept);
        }
        return (lookup);
    }
}

sub vcl_backend_response {
    if (bereq.url ~ "\.(js|css)(\?.*)?$") {
        set beresp.ttl = 10s;
        set beresp.http.Cache-Control = "public, max-age=30";
        
        unset beresp.http.Set-Cookie;
        unset beresp.http.Vary;
        
        set beresp.http.X-Cacheable = "YES";
    }
    
    return (deliver);
}

sub vcl_deliver {
    if (obj.hits > 0) {
        set resp.http.X-Cache = "HIT";
        set resp.http.X-Cache-Hits = obj.hits;
    } else {
        set resp.http.X-Cache = "MISS";
    }
    
    if (req.url ~ "\.(js|css)(\?.*)?$") {
        set resp.http.X-Cache-Key = req.url;
        set resp.http.X-Cache-TTL = obj.ttl;
    }
    
    return (deliver);
}
