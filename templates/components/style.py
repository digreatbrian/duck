from duck.html.components import InnerHtmlComponent

class Style(InnerHtmlComponent):
  def get_element(self):
      return "style"


class AboutUsStyle(Style):
    def on_create(self):
        self.inner_body = """
        #about-us-container {
            display: flex;
            flex-direction: column;
            padding: 20px;
            margin-top: 10px;
        }
        
        #about-us {
            background-image: none !important;
            color: #ccc !important;
            padding: 30px 15px 15px 15px !important;
        }
        """
        
class ContactUsStyle(Style):
    def on_create(self):
        self.inner_body = """
        #contact-us-container {
            display: flex;
            flex-direction: column;
            padding: 20px;
            margin-top: 10px;
        }
        
        #contact-us {
            background-image: none !important;
            color: #ccc !important;
            padding: 30px 15px 15px 15px !important;
        }
        """