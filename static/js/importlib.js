/** Example
// Load scripts globally before app starts

loadScript("myscript.jsx")
  .then(() => console.log("Script loaded successfully"))
  .catch(() => console.error("Failed to load script"));
*/

function loadScript(src, async = true, defer = false, extension_map = {".jsx": "text/babel"}, crossorigin = false) { // Moved crossorigin parameter out of extension_map
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

    if (crossorigin) {
      script.crossOrigin = "anonymous"; // Proper attribute is crossOrigin, not crossorigin
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
    console.log("Script loaded successfully: ", src);
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
    style.href = href; // Correctly assign href
    style.rel = "stylesheet"; // Adding rel attribute for stylesheet
    // async and defer attributes are not applicable for link elements; removed them
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
    console.log("Style loaded successfully: ", href);
  });
}
