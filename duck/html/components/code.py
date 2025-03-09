"""
Code html component.
"""
from duck.html.components import InnerHtmlComponent
from duck.html.components.textarea import TextArea
from duck.html.components.icon import Icon
from duck.html.components.script import Script
from duck.html.components.style import Style
from duck.html.components.container import FlexContainer
from duck.html.components import Theme


class CodeInner(InnerHtmlComponent):
    def get_element(self):
        return "code"


class Code(InnerHtmlComponent):
    """
    Code html component - the base component is built on <pre> tag.
    
    Example Output:
        <pre>
          <code>Code text here</code>
        </pre>
    
    Args:
        code (str): The target code text
        code_props (dict): Dictionary for properties targeting the <code> tag.
        code_style (dict): Dictionary for style targeting the <code> tag.
    """
    def get_element(self):
        return "pre"
    
    def add_initial_components(self):
        self.style["border"] = "1px solid #ccc"
        self.style["border-radius"] = Theme.border_radius
        self.style["display"] = "flex"
        self.style["flex-direction"] = "column"
        self.style["gap"] = "3px"
        self.properties["class"] = "code-block"
        
        # Add code copy button
        self.code_copy_container = FlexContainer()
        self.code_copy_container.style["gap"] = "2px"
        self.code_copy_container.style["justify-content"] = "flex-end"
        self.add_child(self.code_copy_container)
        
        self.code_copy_btn = Icon(icon_class="bi bi-copy")
        self.code_copy_btn.style["width"] = "min-content"
        self.code_copy_btn.style["height"] = "auto"
        self.code_copy_btn.style["position"] = "fixed"
        self.code_copy_btn.style["font-size"] = "1rem"
        self.code_copy_btn.properties["class"] = "code-copy-btn bi bi-copy"
        self.code_copy_btn.properties["onclick"] = "copyCode(this);"
        self.code_copy_container.add_child(self.code_copy_btn)
        
        # Add code inner
        self.code_inner = CodeInner() # <code></code>
        self.code_inner.properties["class"] = "code-block-inner"
        self.add_child(self.code_inner)
        
        # Add global script and style
        script = Script(
            inner_body="""
                function copyCode(copyCodeBtn){
                    const copyBtn = $(copyCodeBtn);
                    const codeBlock = copyCodeBtn.closest('code');
                    //let codeText = codeBlock.text;
                    let initialCopyIconClass = "bi bi-copy"
                    let successCopyIconClass = "bi bi-check"
                    
                    copyBtn.addClass(initialCopyIconClass);
                    copyBtn.removeClass(successCopyIconClass);
                    
                    // copy to clipboard here
                    // remove initial class after copy success
                    copyBtn.removeClass(initialCopyIconClass);
                    copyBtn.addClass(successCopyIconClass);
                    
                    // Schedule reverting to initial icon
                    setTimeout(function () {
                        copyBtn.addClass(initialCopyIconClass);
                        copyBtn.removeClass(successCopyIconClass);
                    }, 2000); // Icon will be reverted after 2 seconds
                }
            """
        )
        
        style = Style(
            inner_body="""
                pre.code-block {
                    padding: 10px;
                }
            """
        )
        self.add_child(script)
        self.add_child(style)
    
    def on_create(self):
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


class EditableCode(Code):
    def on_create(self):
        self.add_initial_components()
        
        # Add textarea
        self.textarea = TextArea()
        self.textarea.style["width"] = "100%"
        self.textarea.style["height"] = "100%"
        self.code_inner.add_child(self.textarea)
        
        if "code" in self.kwargs:
            code = self.kwargs.get('code') or ''
            self.textarea.inner_body += code
        
        if "code_props" in self.kwargs:
            code_props = self.kwargs.get('code_props') or {}
            self.code_inner.properties.update(code_props)
        
        if "code_style" in self.kwargs:
            code_style = self.kwargs.get('code_style') or {}
            self.code_inner.style.update(code_style)
