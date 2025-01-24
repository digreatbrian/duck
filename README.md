# Repository under maintainance!
# 🦆 Duck Webserver and Proxy
![Duck image](./duck/etc/staticfiles/images/duck-default-bw.png)  

**Duck** is a Python-based webserver, framework, and proxy that integrates seamlessly with **Django**. It simplifies web development with built-in HTTPS support, SSL certificate generation, and robust customization options.

## Support This Project towards its completion
![Duck Collaboration Image](./duck-collaboration.jpg)
[![Ko-fi](./support_me_on_kofi_red.png)](https://ko-fi.com/digreatbrian)  
**Please provide your list of features that you would like for this amazing project!**

## ✨ Features

- **Django Integration**: Effortlessly connect with Django projects.

- **Fast**: Duck is fast for asynchronous requests handling, It uses curio to improve performance.

- **HTTPS & SSL**: Easily generate and manage SSL certificates for secure connections.

- **Quick Setup**: Minimal configuration needed to start development.

- **Enhanced Security**: Offers a strong security layer for production servers.

- **Versatile Template Engines**: Supports Jinja2 and Django templates, complete with built-in tags and filters.

- **Logging Options**: Supports file and console-based logging for easier debugging.

- **Reusable HTML Components**: Quickly integrate prebuilt, dynamic, and flexible HTML elements.

- **Extensive Customization**: Easily adjust settings in settings.py for tailored configurations.

- **Task Automation**: Automate repetitive tasks to streamline workflows.

- **Route Blueprints**: Group and organize routes for better readability and project management.
- **Live Reloading**: Automatically restart the server on file changes with **DuckSight Reloader**.
- **React Template Integration**: Seamlessly integrate **React** code into Django or Jinja2 templates.
- **Dual Connection Mode**: Supports handling requests using both **keep-alive** and **close** connection modes.
- **Render Minify Support**: Strips blank newlines and spaces after a template has been rendered thus improving transfer speed.


## 🔧 Upcoming Features

- **SNI Support**: Host multiple websites on the same IP using Server Name Indication.

- **Load Balancer**: Built-in mechanism for distributing traffic using multiple servers and workers (processes for handling requests).

- **Server Analytics**: Monitor and analyze server traffic and statistics.

- **Credential Manager**: Securely store sensitive data like database credentials.

- **Elevate Duck's Online Presence**: Build a dedicated website to foster a thriving community, share knowledge, and streamline access to resources.

- **Remote Server Backends**: Enable proxy compatibility to seamlessly handle client requests via remote servers (currently supports only Django).

- **Admin Site**: Effortlessy manage Duck using customizable administration site.

- **Reusable React Components**: Quickly integrate prebuilt, dynamic, and flexible React components.


## 🚀 Getting Started

### Installation

**Install Duck using pip**:
```sh
pip install --upgrade duck
```
### Requirements

Before using Duck, ensure the following dependencies are installed:
```sh
Django==5.0.6
Jinja2==3.1.3
watchdog==4.0.1
requests>=2.31.0
diskcache
colorama
tzdata # for django time conversions
```
**Additionally, you'll need to have OpenSSL installed on your system for SSL certificate generation**.

### Create a New Project

*To start a new project, run*:

```sh
duck makeproject -n myproject
```

### Duck makeproject modes
1. **Normal project**:  
Create a normal average project.
```sh
duck makeproject -n myproject
```
2. **Mini project**:  
Create a mini version project with lesser files and directories.
```sh
duck makeproject -n myproject --mini
```
3. **Full project**:  
Create a full complete project with all settings and necessary files and directories.
```sh
duck makeproject -n myproject --full
```

*Project structure:*

```
# Full version
myproject/
├── apps/
│   ├── app1/ 
│   │       ├── blueprint.py
│   │       └── views.py
│   └── ...
├── backend/  
│   ├── django/  
│   │   └── duckapp/  
│   │       ├── settings.py  
│   │       ├── urls.py  
│   │       ├── views.py  
│   │       └── ...  
│   └── manage.py
├── etc/
│   ├── ssl/
│   │       ├── server.crt
│   │       └── server.key
│   └── README.md
├── .env
├── .gitignore
├── automations.py
├── main.py  
├── settings.py
├── templatetags.py
├── urls.py
├── views.py
├── requirements.txt
├── LICENSE
├── README.md
└── TODO.md

```

```
# Mini version
myproject/  
├── backend/  
│   ├── django/  
│   │   └── duckapp/  
│   │       ├── settings.py  
│   │       ├── urls.py  
│   │       ├── views.py  
│   │       └── ...  
│   └── manage.py
├── main.py  
├── settings.py
├── urls.py
└── views.py
```

### Running the Server

To start the Duck server, navigate to your project directory and run:
```sh
python main.py
```

*Alternatively, use:*
```sh
$ cd myproject  
$ python3 -m duck runserver -p 8000 -d 'localhost'
```
Then open http://localhost:8000 or https://localhost:8000 if **ENABLE_HTTPS** is enabled in **settings.py**.

**Note**: Running the app from the terminal ignores **main.py** unless explicityly specified using **--file** argument.

You can use **--ipv6** argument to start server on ipv6 address.

*Once you open your browser at the respective url, you should see something like this.*

![Duck local website](./duck/etc/staticfiles/images/local-duck-site.png)

### Example Files

```py
# main.py

from duck.app import App  

app = App(port=5000, addr='127.0.0.1') # App(port=8000, addr='::1', uses_ipv6=True) for ipv6

if __name__ == '__main__':
	app.run()
```

```py
# views.py

def home():  
    return "<h1>Hello world</h1>"
```

```py
# urls.py

from duck.urls import path  
from . import views  

urlpatterns = [  
    path("/", views.home, "home", ["GET"]),  
]

```


## 📘 Blueprints

Organize routes using blueprints for better management. Blueprints let you group URL patterns under a single namespace.

**Note**: Blueprint names determine the route prefix.
For example, a route /home under a blueprint named products becomes /products/home. This behavior may be disabled by parsing set argument `prepend_name_to_url` to False.

**You can create multiple blueprints under same blueprint.py file.**

### 🗺️ Blueprint Structure Example

```
myproject/  
├── some_name/  
│   ├── blueprint.py  
│   └── views.py  
├── main.py  
├── settings.py  
├── urls.py  
└── views.py
```

### Example Blueprint

```py
# blueprint.py

from duck.route import RouteBlueprint  
from . import views  

ProductsBlueprint = RouteBlueprint(name='products') # initialize blueprint

ProductsBlueprint.register_route("/list", views.list_products, name='products-list', methods=["GET"]) # register a normal route to list all products

ProductsBlueprint.re_register_route("media/.*", views.products_media, name='products-media', methods=["GET"]) # register a regex route to serve products media
```

```py
# settings.py

ROUTE_BLUEPRINTS = [  
    "some_name.blueprint.ProductsBlueprint",  
]
```

## 🛠️ Production Recommendations

Use port 80 for HTTP and port 443 for HTTPS in production.

**Secure your SSL configuration for enhanced security.**


## Templates

Duck uses **Jinja2** as the default templating engine, but you can also use **Django templates** if preferred. Additionally, you can create custom template tags and filters within Duck, which will be available for use in both Jinja2 and Django templates.

**Note**:
- To use Duck’s custom tags or filters in a Django-rendered template, include the following at the top of the template:
  ```django
  {% load ducktags %}
 ```


## HTML Components to Use in Templates

Duck provides several HTML components that can be dynamically created and rendered in your templates. These components can be used in both **Jinja2** and **Django** templates.

## Usage Examples

### Jinja2 Template

You can use the HTML components like so in a Jinja2 template:

```jinja
{{ Button(
    style={
        "background-color": "red",
        "color": "white",
    },
    properties={
        "value": "Hello world",
        "id": "btn"
    },
) }}
```

### Django Template

In Django templates, the usage is slightly different, and you need to ensure that the tag is on one line and keyword arguments are quoted as strings:
	
```django
{% Button properties='{"id": "btn", "value": "Hello world"}' style='{"background-color": "blue", "color": "white"}' %}
```

**Note:** In Django templates, make sure the tag is written on a single line and that the keyword arguments are passed as strings (e.g., properties='{"key": "value"}').


## HTML Components Configuration

### Enable HTML Components

By default, HTML components are enabled. You can configure whether to enable or disable the HTML components by setting the ENABLE_HTML_COMPONENTS variable in your settings:
```py
# settings.py

ENABLE_HTML_COMPONENTS: bool = True
```


### Available HTML Components

Duck comes with several pre-defined HTML components that you can use in your templates. These components are mapped to their corresponding classes.

```py
# settings.py

HTML_COMPONENTS: dict[str, str] = {
    "Button": "duck.html.components.button.Button",
    "FlatButton": "duck.html.components.button.FlatButton",
    "RaisedButton": "duck.html.components.button.RaisedButton",
    "Input": "duck.html.components.input.Input",
    "CSRFInput": "duck.html.components.input.CSRFInput",
    "Checkbox": "duck.html.components.checkbox.Checkbox",
    "Select": "duck.html.components.select.Select",
    "TextArea": "duck.html.components.textarea.TextArea",
}
```


## Creating Custom HTML Components

If you want to create your own HTML components, you can subclass one of Duck's base component classes: InnerHtmlComponent or NoInnerHtmlComponent.

### Example: Creating a Custom Button Component
```py
from duck.html.components import InnerHtmlComponent

class CustomButton(InnerHtmlComponent):
    """
    CustomHTML Button component.
    """
    def __init__(self, properties: dict[str, str] = {}, style: dict[str, str] = {}):
        """
        Initialize the Button component with optional properties and style.
        """
        btn_style = {
            "padding": "10px 20px",
            "cursor": "pointer",
            "transition": "background-color 0.3s ease",
            "border": "none",
        }  # Default style

        btn_style.update(style) if style else None  # Update default style with custom styles

        super().__init__("button", properties, btn_style)
```

**InnerHtmlComponent:** This is used when your HTML component has inner content, like a button or a div. You can define the content and the styles inside this component.

**NoInnerHtmlComponent:** This is used for self-closing tags, like inputs or checkboxes, where there’s no inner HTML content.


### How the Classes Work

**InnerHtmlComponent:** This is used for components that contain inner HTML (e.g., buttons, divs).  

**NoInnerHtmlComponent:** This is used for components that do not contain inner HTML (e.g., input fields, checkboxes).

---

This setup makes it easy to add reusable HTML components to your templates and customize their appearance and behavior by simply passing properties and styles. You can also extend this by creating custom components to suit your needs.

## Troubleshooting Tips:

### SSL Certificate Issues:
If SSL certificates are not being generated, ensure that OpenSSL is installed correctly on your machine. You can verify OpenSSL with:

```sh
openssl version
```

Also, check the permissions of the etc/ssl directory to ensure the webserver can write the certificates.

### Port Conflicts:
If the server fails to start due to a port conflict, check if the port is already in use by another service. You can specify an alternative port by passing the -p <port> argument:

```sh
python3 -m duck runserver -p 8080
```


## 📜 License

**Duck** is licensed under the BSD License. See the [LICENSE](./LICENSE) file for details.


## 💬 Support

For questions or issues, please open an issue on the **Duck GitHub repository**.

---

**Start building secure, scalable, and customizable web applications with Duck today!**
