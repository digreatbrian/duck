# Duck Framework
![Duck image](./images/duck-cover.png)  

**Duck** is a powerful, open-source, Python-based **web server**, **framework**, and **reverse proxy** designed for building modern, customizable web applications — from small sites to large-scale platforms — with seamless **Django** integration.

It simplifies web development with:

- **Built-in HTTPS support** for secure connections.
- **Native HTTP/2 support** [🔗](https://duckframework.xyz/documentation/free_ssl_certificate.html)
- Hassle-free **free SSL certificate generation** with **automatic renewal** [🔗](https://duckframework.xyz/documentation/free_ssl_certificate.html)
- Integrated **server-side** component system inspired by [React.js](https://react.dev), plus [prebuilt, ready to use components](https://duckframework.xyz/documentation/predefined_components.html).
- Built-in [task automation](https://duckframework.xyz/documentation/automations.html) — no need for [**cron jobs**](https://en.m.wikipedia.org/wiki/Cron).
- Highly **customizable** to suit any project.

- And much more — explore all features on the  [official site](https://duckframework.xyz/features)

Designed for speed and security, **Duck** lets you deploy scalable, high-performance web applications with minimal setup.

Perfect for developers who want secure, flexible, and production-ready web solutions — all in one tool.


## Getting Started

Install **Duck** using pip:

```sh
pip install git+https://github.com/digreatbrian/duck.git
```

## Simple startup

```sh
duck makeproject myproject
duck runserver
```
This starts a server on port **80**. Navigate to [http://localhost:80](http://localhost:80) in your browser.

By default, a basic site is displayed — but there's much more you can do.  
Explore the full capabilities in the [documentation](https://duckframework.xyz/documentation).

By default, Duck automatically compresses [**streaming responses**](https://www.cloudflare.com/learning/video/what-is-http-live-streaming/#:~:text=With%20streaming%20over%20HTTP%2C%20the,every%20segment%20of%20video%20data.) (e.g. large files and media streams) to improve performance. In rare cases, this may cause issues. You can disable this behavior by setting `compress_streaming_responses` to `False`:

```py
# settings.py

CONTENT_COMPRESSION: dict[str] = {
    "encoding": "gzip",
    "min_size": 1024,  # files more than 1KB
    "max_size": 512 * 1024,  # files not more than 512KB
    "level": 5,
    "vary_on": True,  # Whether to include Vary header in response
    "compress_streaming_responses": False,
    "mimetypes": [
        "text/html",
        "text/css",
        "application/javascript",
        "application/json",
        "application/xml",
        "application/xhtml+xml",
        "application/rss+xml",
        "application/atom+xml",
    ],  # avoid compressing already compressed files like images
}
```

## Duck Official Site

You can visit **Duck's** official website for more information at [Duck official site](https://duckframework.xyz).

Jump straight to [Documentation](https://duckframework.xyz/documentation).

## Contribution and Issues
**Duck** is currently accepting any kind of contribution either financially or any other contributions.  

For financial contributions, navigate to [sponsorship](https://duckframework.xyz/sponsorship) page.

> **Duck** is looking for a contributor to create a high-quality YouTube video introducing the framework.  
This video will be featured on the official Duck website and may be used in future promotions.

> If you're interested, [send an email](digreatbrian@gmail.com) with a link to your video. Please include a brief message about the purpose of your email.

### Issues

For any issues, feel free to report these at [issues](https://github.com/digreatbrian/duck/issues) page.

#### **Duck** is updated and improved frequently, check out this repo more oftenly for bug fixes & improvements.
