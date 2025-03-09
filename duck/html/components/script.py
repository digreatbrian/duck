"""
Script html component.
"""

from duck.html.components import InnerHtmlComponent


class Script(InnerHtmlComponent):
  """
  Script html component.
  
  Example Usage:
      script = Script(
          inner_body='''
              function someFunction(){
                  // your implementation here.
              }
          '''
      )
      component.add_child(script)
  """
  def get_element(self):
      return "script"
