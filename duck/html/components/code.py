"""
HTML Code Component Classes.

These classes represent a code block component that can be embedded within an HTML page.
They provide functionality to display code with options for styling, interactivity, and copying code to the clipboard.

Classes:
    - CodeInner: Represents the inner `<code>` element within a `<pre>` tag.
    - Code: The base code block component, wrapped in a `<pre>` tag, with a copy button functionality.
    - EditableCode: Extends the `Code` component, allowing the code block to be editable.

Usage:
    - Code: Display static code with copy functionality.
    - EditableCode: Display editable code with copy functionality.

Example:
    ```python
    code_block = Code(code="print('Hello, world!')", code_props={"class": "highlighted"})
    editable_code_block = EditableCode(code="x = 5", code_style={"color": "blue"})
    ```
"""
from duck.html.components import InnerHtmlComponent
from duck.html.components.textarea import TextArea
from duck.html.components.icon import Icon
from duck.html.components.script import Script
from duck.html.components.style import Style
from duck.html.components.container import FlexContainer
from duck.html.components import Theme


class CodeInner(InnerHtmlComponent):
    """
    Represents the inner <code> element in the HTML code block.

    This component is a simple representation of the <code> tag used inside the <pre> tag for code display.
    """
    def get_element(self):
        return "code"


class Code(InnerHtmlComponent):
    """
    Code HTML component - The base component is built on the <pre> tag.
    
    This component is used to display a block of code inside a `<pre>` tag, with a copy-to-clipboard button and 
    customizable properties for the code block and its inner `<code>` tag.

    Example Output:
        <pre>
          <code>Code text here</code>
        </pre>

    Args:
        code (str): The target code text that will be displayed inside the code block.
        code_props (dict): Dictionary of properties that will be applied to the <code> tag (e.g., `{"class": "highlighted"}`).
        code_style (dict): Dictionary of styles that will be applied to the <code> tag (e.g., `{"color": "blue"}`).

    Methods:
        add_initial_components: Adds initial components like styling, copy button, and script.
        on_create: Sets the initial content and properties for the code block.

    Attributes:
        code_copy_container (FlexContainer): Container for the copy button.
        code_copy_btn (Icon): The icon used as a button to trigger copying of the code.
        code_inner (CodeInner): The inner code block inside the `<pre>` tag.
    """
    
    def get_element(self):
        return "pre"
    
    def add_initial_components(self):
        """
        Adds initial styling and components such as the copy button and the `<code>` element.
        """
        # Add default styling for the code block
        self.style["border"] = "1px solid #ccc"
        self.style["border-radius"] = Theme.border_radius
        self.style["display"] = "flex"
        self.style["flex-direction"] = "column"
        self.style["gap"] = "3px"
        self.style["padding"] = "10px"
        self.properties["class"] = "code-block"
        
        # Add copy button container
        self.code_copy_container = FlexContainer()
        self.code_copy_container.style["gap"] = "2px"
        self.code_copy_container.style["justify-content"] = "flex-end"
        self.add_child(self.code_copy_container)
        
        # Add the copy button (icon)
        self.code_copy_btn = Icon(icon_class="bi bi-copy")
        self.code_copy_btn.style["width"] = "min-content"
        self.code_copy_btn.style["height"] = "auto"
        self.code_copy_btn.style["position"] = "fixed"
        self.code_copy_btn.style["font-size"] = "1rem"
        self.code_copy_btn.properties["class"] = "code-copy-btn bi bi-copy"
        self.code_copy_btn.properties["onclick"] = "copyCode(this);"
        self.code_copy_container.add_child(self.code_copy_btn)
        
        # Add inner code element (<code></code>)
        self.code_inner = CodeInner()  # <code></code>
        self.code_inner.properties["class"] = "code-block-inner"
        self.add_child(self.code_inner)
        
        # Add global script for copying code
        script = Script(
            inner_body="""
                function copyCode(copyCodeBtn){
                    const copyBtn = $(copyCodeBtn);
                    const codeBlock = copyCodeBtn.closest('code');
                    let initialCopyIconClass = "bi bi-copy";
                    let successCopyIconClass = "bi bi-check";
                    
                    copyBtn.addClass(initialCopyIconClass);
                    copyBtn.removeClass(successCopyIconClass);
                    
                    // Copy the content to clipboard here (use Clipboard API)
                    navigator.clipboard.writeText(codeBlock.innerText)
                        .then(() => {
                            copyBtn.removeClass(initialCopyIconClass);
                            copyBtn.addClass(successCopyIconClass);
                            setTimeout(function () {
                                copyBtn.addClass(initialCopyIconClass);
                                copyBtn.removeClass(successCopyIconClass);
                            }, 2000); // Icon reverts after 2 seconds
                        })
                        .catch(err => {
                            console.error("Failed to copy text: ", err);
                        });
                }
            """
        )
        self.add_child(script)
        
    def on_create(self):
        """
        Initializes the components and sets up the code content.
        It checks if the `code`, `code_props`, and `code_style` arguments were passed in.
        """
        self.add_initial_components()
        
        if "code" in self.kwargs:
            code = self.kwargs.get('code') or ''
            self.code_inner.inner_body += code
        
        if "code_props" in self.kwargs:
            code_props = self.kwargs.get('code_props') or {}
            self.code_inner.properties.update(code_props)
        
        if "code_style" in self.kwargs:
            code_style = self.kwargs.get('code_style') or {}
            self.code_inner.style.update(code_style)
        
        if "disable_copy_button" in self.kwargs and self.kwargs.get("disable_copy_button"):
            self.remove_child(self.code_copy_container)


class EditableCode(Code):
    """
    Editable version of the Code component.

    This component extends the base `Code` component and adds the ability to edit the code directly.
    The `<pre>` block and the `<code>` block are both made content-editable.

    Example:
        editable_code = EditableCode(code="print('Hello, world!')", code_style={"color": "green"})
    
    Args:
        code (str): The target code text.
        code_style (dict): Dictionary for styling the <code> element (e.g., `{"color": "red"}`).
    
    Methods:
        on_create: Extends the `Code.on_create` method and adds the `contenteditable` attribute.
    """
    def on_create(self):
        """
        Extends the on_create method to add the 'contenteditable' attribute to allow code editing.
        """
        super().on_create()
        self.properties["contenteditable"] = "true"
