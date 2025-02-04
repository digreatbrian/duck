/** Example
// Load scripts globally before app starts

loadScript("myscript.jsx")
  .then(() => console.log("Script loaded successfully"))
  .catch(() => console.error("Failed to load script"));
*/

function loadScript(src, async = true, defer = false, extension_map = {".jsx": "text/babel", crossorigin: false}) {
  return new Promise((resolve, reject) => {
    // Check if the script is already loaded
    if (document.querySelector(`script[src="${src}"]`)) {
      resolve(); // Script already exists
      return;
    }

    const script = document.createElement("script");
    script.src = src;
    script.async = async;
    script.defer = defer;
    script.onload = resolve;
    script.onerror = reject;

    if (crossorigin){
      script.crossorigin = crossorigin;
    }

    // Loop through extension_map to determine the script type based on the file extension
    Object.keys(extension_map).forEach((ext) => {
      if (src.endsWith(ext)) {
        script.type = extension_map[ext];
        return; // Once matched, stop the loop
      }
    });

    // Append the script tag to the document body
    document.body.appendChild(script);
  });
}


function loadStyle(href, async = true, defer = false, extension_map = {".css": "text/css"}) {
  return new Promise((resolve, reject) => {
    // Check if the style is already loaded
    if (document.querySelector(`link[href="${href}"]`)) {
      resolve(); // Style already exists
      return;
    }

    const style = document.createElement("link");
    style.style = style;
    style.async = async;
    style.defer = defer;
    style.onload = resolve;
    style.onerror = reject;

    // Loop through extension_map to determine the style type based on the file extension
    Object.keys(extension_map).forEach((ext) => {
      if (href.endsWith(ext)) {
        style.type = extension_map[ext];
        return; // Once matched, stop the loop
      }
    });

    // Append the style tag to the document body
    document.body.appendChild(style);
  });
}
