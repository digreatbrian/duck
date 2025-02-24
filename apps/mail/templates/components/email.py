from templates.components.container import FlexContainer, Container
from templates.components.card import Card
from templates.components.image import Image
from templates.components.style import Style
from templates.components.script import Script
from templates.components.icon import Icon
from templates.components.footer import Footer


class SimpleEmail(Container):
    def on_create(self):
        # Start the email body structure with a table for layout
        self.inner_body += """
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border-collapse: collapse; background-color: rgba(100, 100, 100, .35); color: #ccc; font-family: ui-rounded; text-align: center; border: 1px solid #ccc; border-radius: 8px; padding: 10px;">
        <tr>
            <td style="text-align: center; padding: 20px;">
        """
        
        # Add the heading if provided
        if "heading" in self.kwargs:
            self.inner_body += "<h3 style='margin: 0; padding: 5px;'>" + self.kwargs.get("heading", "") + "</h3>"
        
        # Add the subheading if provided
        if "subheading" in self.kwargs:
            self.inner_body += "<h4 style='margin: 0; padding: 5px;'>" + self.kwargs.get("subheading", "") + "</h4>"
        
        # Add the body content if provided
        if "body" in self.kwargs:
            self.inner_body += "<p style='margin: 0; padding: 5px;'>" + self.kwargs.get("body", "") + "</p>"
        
        # Add footer content
        footer = Footer()  # Assuming Footer is another class you are using
        self.inner_body += footer.to_string()

        # End the table structure
        self.inner_body += """
            </td>
        </tr>
        </table>
        """

        # Add global styles (inline styles for email clients)
        self.inner_body += """
        <style type="text/css">
            body {
                margin: 0;
                padding: 0;
                width: 100%;
                background-color: black;
                color: #ccc;
                font-family: ui-rounded, Arial, sans-serif;
            }
        </style>
        """
