"""
Style html component.
"""
from duck.html.components import InnerHtmlComponent


class Style(InnerHtmlComponent):
  """
  Style html component.
  
  Example Usage:
      style = Style(
          inner_body='''
              .some-class {
                  /* implementation here */
              }
          '''
      )
      component.add_child(style)
  """
  def get_element(self):
      return "style"
