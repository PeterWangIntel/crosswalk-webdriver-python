__all__ = ["kFocusScript", \
           "kGetElementRegionScript", \
           "kIsOptionElementToggleableScript", \
           "kExecuteAsyncScriptScript", \
           "kAddCookieScript", \
           "kCallFunctionScript", \
           "kDispatchContextMenuEventScript"]

kFocusScript =\
    "function() { // Copyright (c) Modify as our own signature. All rights reserved.\n"\
    "// Use of this source code is governed by a BSD-style license that can be\n"\
    "// found in the LICENSE file.\n"\
    "\n"\
    "function focus(element) {\n"\
    "  // Focus the target element in order to send keys to it.\n"\
    "  // First, the currently active element is blurred, if it is different from\n"\
    "  // the target element. We do not want to blur an element unnecessarily,\n"\
    "  // because this may cause us to lose the current cursor position in the\n"\
    "  // element.\n"\
    "  // Secondly, we focus the target element.\n"\
    "  // Thirdly, if the target element is newly focused and is a text input, we\n"\
    "  // set the cursor position at the end.\n"\
    "  // Fourthly, we check if the new active element is the target element. If not,\n"\
    "  // we throw an error.\n"\
    "  // Additional notes:\n"\
    "  //   - |document.activeElement| is the currently focused element, or body if\n"\
    "  //     no element is focused\n"\
    "  //   - Even if |document.hasFocus()| returns true and the active element is\n"\
    "  //     the body, sometimes we still need to focus the body element for send\n"\
    "  //     keys to work. Not sure why\n"\
    "  //   - You cannot focus a descendant of a content editable node\n"\
    "  //   - V8 throws a TypeError when calling setSelectionRange for a non-text\n"\
    "  //     input, which still have setSelectionRange defined. For xwalk 29+, V8\n"\
    "  //     throws a DOMException with code InvalidStateError.\n"\
    "  var doc = element.ownerDocument || element;\n"\
    "  var prevActiveElement = doc.activeElement;\n"\
    "  if (element != prevActiveElement && prevActiveElement)\n"\
    "    prevActiveElement.blur();\n"\
    "  element.focus();\n"\
    "  if (element != prevActiveElement && element.value &&\n"\
    "      element.value.length && element.setSelectionRange) {\n"\
    "    try {\n"\
    "      element.setSelectionRange(element.value.length, element.value.length);\n"\
    "    } catch (error) {\n"\
    "      if (!(error instanceof TypeError) && !(error instanceof DOMException &&\n"\
    "          error.code == DOMException.INVALID_STATE_ERR))\n"\
    "        throw error;\n"\
    "    }\n"\
    "  }\n"\
    "  if (element != doc.activeElement)\n"\
    "    throw new Error('cannot focus element');\n"\
    "}\n"\
    "; return focus.apply(null, arguments) }\n"
kGetElementRegionScript =\
    "function() { // Copyright (c) Modifiy to our own signature. All rights reserved.\n"\
    "// Use of this source code is governed by a BSD-style license that can be\n"\
    "// found in the LICENSE file.\n"\
    "\n"\
    "function getElementRegion(element) {\n"\
    "  // Check that node type is element.\n"\
    "  if (element.nodeType != 1)\n"\
    "    throw new Error(element + ' is not an element');\n"\
    "\n"\
    "  // We try 2 methods to determine element region. Try the first client rect,\n"\
    "  // and then the bounding client rect.\n"\
    "  // SVG is one case that doesn't have a first client rect.\n"\
    "  var clientRects = element.getClientRects();\n"\
    "  if (clientRects.length == 0) {\n"\
    "    var box = element.getBoundingClientRect();\n"\
    "    if (element.tagName.toLowerCase() == 'area') {\n"\
    "      var coords = element.coords.split(',');\n"\
    "      if (element.shape.toLowerCase() == 'rect') {\n"\
    "        if (coords.length != 4)\n"\
    "          throw new Error('failed to detect the region of the area');\n"\
    "        var leftX = Number(coords[0]);\n"\
    "        var topY = Number(coords[1]);\n"\
    "        var rightX = Number(coords[2]);\n"\
    "        var bottomY = Number(coords[3]);\n"\
    "        return {\n"\
    "            'left': leftX,\n"\
    "            'top': topY,\n"\
    "            'width': rightX - leftX,\n"\
    "            'height': bottomY - topY\n"\
    "        };\n"\
    "      } else if (element.shape.toLowerCase() == 'circle') {\n"\
    "        if (coords.length != 3)\n"\
    "          throw new Error('failed to detect the region of the area');\n"\
    "        var centerX = Number(coords[0]);\n"\
    "        var centerY = Number(coords[1]);\n"\
    "        var radius = Number(coords[2]);\n"\
    "        return {\n"\
    "            'left': Math.max(0, centerX - radius),\n"\
    "            'top': Math.max(0, centerY - radius),\n"\
    "            'width': radius * 2,\n"\
    "            'height': radius * 2\n"\
    "        };\n"\
    "      } else if (element.shape.toLowerCase() == 'poly') {\n"\
    "        if (coords.length < 2)\n"\
    "          throw new Error('failed to detect the region of the area');\n"\
    "        var minX = Number(coords[0]);\n"\
    "        var minY = Number(coords[1]);\n"\
    "        var maxX = minX;\n"\
    "        var maxY = minY;\n"\
    "        for (i = 2; i < coords.length; i += 2) {\n"\
    "          var x = Number(coords[i]);\n"\
    "          var y = Number(coords[i + 1]);\n"\
    "          minX = Math.min(minX, x);\n"\
    "          minY = Math.min(minY, y);\n"\
    "          maxX = Math.max(maxX, x);\n"\
    "          maxY = Math.max(maxY, y);\n"\
    "        }\n"\
    "        return {\n"\
    "            'left': minX,\n"\
    "            'top': minY,\n"\
    "            'width': maxX - minX,\n"\
    "            'height': maxY - minY\n"\
    "        };\n"\
    "      } else {\n"\
    "        throw new Error('shape=' + element.shape + ' is not supported');\n"\
    "      }\n"\
    "    }\n"\
    "    return {\n"\
    "        'left': 0,\n"\
    "        'top': 0,\n"\
    "        'width': box.width,\n"\
    "        'height': box.height\n"\
    "    };\n"\
    "  } else {\n"\
    "    var clientRect = clientRects[0];\n"\
    "    var box = element.getBoundingClientRect();\n"\
    "    return {\n"\
    "        'left': clientRect.left - box.left,\n"\
    "        'top': clientRect.top - box.top,\n"\
    "        'width': clientRect.right - clientRect.left,\n"\
    "        'height': clientRect.bottom - clientRect.top\n"\
    "    };\n"\
    "  }\n"\
    "}\n"\
    "; return getElementRegion.apply(null, arguments) }\n"
kIsOptionElementToggleableScript =\
    "function() { // Copyright (c) Modify to our own signature. All rights reserved.\n"\
    "// Use of this source code is governed by a BSD-style license that can be\n"\
    "// found in the LICENSE file.\n"\
    "\n"\
    "function isOptionElementToggleable(option) {\n"\
    "  if (option.tagName.toLowerCase() != 'option')\n"\
    "    throw new Error('element is not an option');\n"\
    "  for (var parent = option.parentElement;\n"\
    "       parent;\n"\
    "       parent = parent.parentElement) {\n"\
    "    if (parent.tagName.toLowerCase() == 'select') {\n"\
    "      return parent.multiple;\n"\
    "    }\n"\
    "  }\n"\
    "  throw new Error('option element is not in a select');\n"\
    "}\n"\
    "; return isOptionElementToggleable.apply(null, arguments) }\n"
kExecuteAsyncScriptScript =\
    "function() { // Copyright (c) Modify to our own signature. All rights reserved.\n"\
    "// Use of this source code is governed by a BSD-style license that can be\n"\
    "// found in the LICENSE file.\n"\
    "\n"\
    "/**\n"\
    " * Enum for WebDriver status codes.\n"\
    " * @enum {number}\n"\
    " */\n"\
    "var StatusCode = {\n"\
    "  OK: 0,\n"\
    "  UNKNOWN_ERROR: 13,\n"\
    "  JAVASCRIPT_ERROR: 17,\n"\
    "  SCRIPT_TIMEOUT: 28,\n"\
    "};\n"\
    "\n"\
    "/**\n"\
    " * Dictionary key for asynchronous script info.\n"\
    " * @const\n"\
    " */\n"\
    "var ASYNC_INFO_KEY = '$xwalk_asyncScriptInfo';\n"\
    "\n"\
    "/**\n"\
    "* Return the information of asynchronous script execution.\n"\
    "*\n"\
    "* @return {Object.<string, ?>} Information of asynchronous script execution.\n"\
    "*/\n"\
    "function getAsyncScriptInfo() {\n"\
    "  if (!(ASYNC_INFO_KEY in document))\n"\
    "    document[ASYNC_INFO_KEY] = {'id': 0};\n"\
    "  return document[ASYNC_INFO_KEY];\n"\
    "}\n"\
    "\n"\
    "/**\n"\
    "* Execute the given script and save its asynchronous result.\n"\
    "*\n"\
    "* If script1 finishes after script2 is executed, then script1's result will be\n"\
    "* discarded while script2's will be saved.\n"\
    "*\n"\
    "* @param {string} script The asynchronous script to be executed. The script\n"\
    "*     should be a proper function body. It will be wrapped in a function and\n"\
    "*     invoked with the given arguments and, as the final argument, a callback\n"\
    "*     function to invoke to report the asynchronous result.\n"\
    "* @param {!Array.<*>} args Arguments to be passed to the script.\n"\
    "* @param {boolean} isUserSupplied Whether the script is supplied by the user.\n"\
    "*     If not, UnknownError will be used instead of JavaScriptError if an\n"\
    "*     exception occurs during the script, and an additional error callback will\n"\
    "*     be supplied to the script.\n"\
    "* @param {?number} opt_timeoutMillis The timeout, in milliseconds, to use.\n"\
    "*     If the timeout is exceeded and the callback has not been invoked, a error\n"\
    "*     result will be saved and future invocation of the callback will be\n"\
    "*     ignored.\n"\
    "*/\n"\
    "function executeAsyncScript(script, args, isUserSupplied, opt_timeoutMillis) {\n"\
    "  var info = getAsyncScriptInfo();\n"\
    "  info.id++;\n"\
    "  delete info.result;\n"\
    "  var id = info.id;\n"\
    "\n"\
    "  function report(status, value) {\n"\
    "    if (id != info.id)\n"\
    "      return;\n"\
    "    info.id++;\n"\
    "    info.result = {status: status, value: value};\n"\
    "  }\n"\
    "  function reportValue(value) {\n"\
    "    report(StatusCode.OK, value);\n"\
    "  }\n"\
    "  function reportScriptError(error) {\n"\
    "    var code = isUserSupplied ? StatusCode.JAVASCRIPT_ERROR :\n"\
    "                                (error.code || StatusCode.UNKNOWN_ERROR);\n"\
    "    var message = error.message;\n"\
    "    if (error.stack) {\n"\
    "      message += \"\\nJavaScript stack:\\n\" + error.stack;\n"\
    "    }\n"\
    "    report(code, message);\n"\
    "  }\n"\
    "  args.push(reportValue);\n"\
    "  if (!isUserSupplied)\n"\
    "    args.push(reportScriptError);\n"\
    "\n"\
    "  try {\n"\
    "    new Function(script).apply(null, args);\n"\
    "  } catch (error) {\n"\
    "    reportScriptError(error);\n"\
    "    return;\n"\
    "  }\n"\
    "\n"\
    "  if (typeof(opt_timeoutMillis) != 'undefined') {\n"\
    "    window.setTimeout(function() {\n"\
    "      var code = isUserSupplied ? StatusCode.SCRIPT_TIMEOUT :\n"\
    "                                  StatusCode.UNKNOWN_ERROR;\n"\
    "      var errorMsg = 'result was not received in ' + opt_timeoutMillis / 1000 +\n"\
    "                     ' seconds';\n"\
    "      report(code, errorMsg);\n"\
    "    }, opt_timeoutMillis);\n"\
    "  }\n"\
    "}\n"\
    "; return executeAsyncScript.apply(null, arguments) }\n"
kAddCookieScript =\
    "function() { // Copyright (c) Modify to our own signature. All rights reserved.\n"\
    "// Use of this source code is governed by a BSD-style license that can be\n"\
    "// found in the LICENSE file.\n"\
    "\n"\
    "/**\n"\
    "* Test whether the given domain is valid for a cookie.\n"\
    "*\n"\
    "* @param {string} domain Domain for a cookie.\n"\
    "* @return {boolean} True if the domain is valid, otherwise false.\n"\
    "*/\n"\
    "function isDomainValid(domain) {\n"\
    "  var dummyCookie = 'XwalkDriverwjers908fljsdf37459fsdfgdfwru=';\n"\
    "\n"\
    "  document.cookie = dummyCookie + '; domain=' + domain;\n"\
    "  if (document.cookie.indexOf(dummyCookie) != -1) {\n"\
    "    // Expire the dummy cookie if it is added successfully.\n"\
    "    document.cookie = dummyCookie + '; Max-Age=0';\n"\
    "    return true;\n"\
    "  }\n"\
    "  return false;\n"\
    "}\n"\
    "\n"\
    "/**\n"\
    "* Add the given cookie to the current web page.\n"\
    "*\n"\
    "* If path is not specified, default to '/'.\n"\
    "* If domain is not specified, default to document.domain, otherwise remove its\n"\
    "* port number.\n"\
    "*\n"\
    "* Validate name, value, domain and path of the cookie in the same way as the\n"\
    "* method CanonicalCookie::Create in src/net/cookies/canonical_cookie.cc. Besides\n"\
    "* the following requirements, name, value, domain and path of the cookie should\n"\
    "* not start or end with ' ' or '\\t', and should not contain '\\n', '\\r', or '\\0'.\n"\
    "* <ul>\n"\
    "* <li>name: no ';' or '='\n"\
    "* <li>value: no ';'\n"\
    "* <li>path: starts with '/', no ';'\n"\
    "* </ul>\n"\
    "*\n"\
    "* @param {!Object} cookie An object representing a Cookie JSON Object as\n"\
    "*     specified in https://code.google.com/p/selenium/wiki/JsonWireProtocol.\n"\
    "*/\n"\
    "function addCookie(cookie) {\n"\
    "  function isNameInvalid(value) {\n"\
    "    return /(^[ \\t])|([;=\\n\\r\\0])|([ \\t]$)/.test(value);\n"\
    "  }\n"\
    "  function isValueInvalid(value) {\n"\
    "    return /(^[ \\t])|([;\\n\\r\\0])|([ \\t]$)/.test(value);\n"\
    "  }\n"\
    "  function isPathInvalid(path) {\n"\
    "    return path[0] != '/' || /([;\\n\\r\\0])|([ \\t]$)/.test(path);\n"\
    "  }\n"\
    "\n"\
    "  var name = cookie['name'];\n"\
    "  if (!name || isNameInvalid(name))\n"\
    "    throw new Error('name of cookie is missing or invalid:\"' + name + '\"');\n"\
    "\n"\
    "  var value = cookie['value'] || '';\n"\
    "  if (isValueInvalid(value))\n"\
    "    throw new Error('value of cookie is invalid:\"' + value + '\"');\n"\
    "\n"\
    "  var domain = cookie['domain'];\n"\
    "  // Remove the port number from domain.\n"\
    "  if (domain) {\n"\
    "    var domain_parts = domain.split(':');\n"\
    "    if (domain_parts.length > 2)\n"\
    "      throw new Error('domain of cookie has too many colons');\n"\
    "    else if (domain_parts.length == 2)\n"\
    "      domain = domain_parts[0];\n"\
    "  }\n"\
    "  // Validate domain.\n"\
    "  if (domain && (isValueInvalid(domain) || !isDomainValid(domain))) {\n"\
    "    var error = new Error();\n"\
    "    error.code = 24;  // Error code for InvalidCookieDomain.\n"\
    "    error.message = 'invalid domain:\"' + domain + '\"';\n"\
    "    throw error;\n"\
    "  }\n"\
    "\n"\
    "  var path = cookie['path'];\n"\
    "  if (path && isPathInvalid(path))\n"\
    "    throw new Error('path of cookie is invalid:\"' + path + '\"');\n"\
    "\n"\
    "  var newCookie = name + '=' + value;\n"\
    "  newCookie += '; path=' + (path || '/');\n"\
    "  newCookie += '; domain=' + (domain || document.domain);\n"\
    "  if (cookie['expiry']) {\n"\
    "    var expiredDate = new Date(cookie['expiry'] * 1000);\n"\
    "    newCookie += '; expires=' + expiredDate.toUTCString();\n"\
    "  }\n"\
    "  if (cookie['secure'])\n"\
    "    newCookie += '; secure';\n"\
    "\n"\
    "  document.cookie = newCookie;\n"\
    "}\n"\
    "; return addCookie.apply(null, arguments) }\n"
kCallFunctionScript =\
    "function() { // Copyright (c) Modify to our own signature. All rights reserved.\n"\
    "// Use of this source code is governed by a BSD-style license that can be\n"\
    "// found in the LICENSE file.\n"\
    "\n"\
    "/**\n"\
    " * Enum for WebDriver status codes.\n"\
    " * @enum {number}\n"\
    " */\n"\
    "var StatusCode = {\n"\
    "  STALE_ELEMENT_REFERENCE: 10,\n"\
    "  UNKNOWN_ERROR: 13,\n"\
    "};\n"\
    "\n"\
    "/**\n"\
    " * Enum for node types.\n"\
    " * @enum {number}\n"\
    " */\n"\
    "var NodeType = {\n"\
    "  ELEMENT: 1,\n"\
    "  DOCUMENT: 9,\n"\
    "};\n"\
    "\n"\
    "/**\n"\
    " * Dictionary key to use for holding an element ID.\n"\
    " * @const\n"\
    " * @type {string}\n"\
    " */\n"\
    "var ELEMENT_KEY = 'ELEMENT';\n"\
    "\n"\
    "/**\n"\
    " * True if shadow dom is enabled.\n"\
    " * @const\n"\
    " * @type {boolean}\n"\
    " */\n"\
    "var SHADOW_DOM_ENABLED = typeof WebKitShadowRoot === 'function';\n"\
    "\n"\
    "/**\n"\
    " * A cache which maps IDs <-> cached objects for the purpose of identifying\n"\
    " * a script object remotely.\n"\
    " * @constructor\n"\
    " */\n"\
    "function Cache() {\n"\
    "  this.cache_ = {};\n"\
    "  this.nextId_ = 1;\n"\
    "  this.idPrefix_ = Math.random().toString();\n"\
    "}\n"\
    "\n"\
    "Cache.prototype = {\n"\
    "\n"\
    "  /**\n"\
    "   * Stores a given item in the cache and returns a unique ID.\n"\
    "   *\n"\
    "   * @param {!Object} item The item to store in the cache.\n"\
    "   * @return {number} The ID for the cached item.\n"\
    "   */\n"\
    "  storeItem: function(item) {\n"\
    "    for (var i in this.cache_) {\n"\
    "      if (item == this.cache_[i])\n"\
    "        return i;\n"\
    "    }\n"\
    "    var id = this.idPrefix_  + '-' + this.nextId_;\n"\
    "    this.cache_[id] = item;\n"\
    "    this.nextId_++;\n"\
    "    return id;\n"\
    "  },\n"\
    "\n"\
    "  /**\n"\
    "   * Retrieves the cached object for the given ID.\n"\
    "   *\n"\
    "   * @param {number} id The ID for the cached item to retrieve.\n"\
    "   * @return {!Object} The retrieved item.\n"\
    "   */\n"\
    "  retrieveItem: function(id) {\n"\
    "    var item = this.cache_[id];\n"\
    "    if (item)\n"\
    "      return item;\n"\
    "    var error = new Error('not in cache');\n"\
    "    error.code = StatusCode.STALE_ELEMENT_REFERENCE;\n"\
    "    error.message = 'element is not attached to the page document';\n"\
    "    throw error;\n"\
    "  },\n"\
    "\n"\
    "  /**\n"\
    "   * Clears stale items from the cache.\n"\
    "   */\n"\
    "  clearStale: function() {\n"\
    "    for (var id in this.cache_) {\n"\
    "      var node = this.cache_[id];\n"\
    "      if (!this.isNodeReachable_(node))\n"\
    "        delete this.cache_[id];\n"\
    "    }\n"\
    "  },\n"\
    "\n"\
    "  /**\n"\
    "    * @private\n"\
    "    * @param {!Node} node The node to check.\n"\
    "    * @return {boolean} If the nodes is reachable.\n"\
    "    */\n"\
    "  isNodeReachable_: function(node) {\n"\
    "    var nodeRoot = getNodeRoot(node);\n"\
    "    if (nodeRoot == document)\n"\
    "      return true;\n"\
    "    else if (SHADOW_DOM_ENABLED && nodeRoot instanceof WebKitShadowRoot)\n"\
    "      return true;\n"\
    "\n"\
    "    return false;\n"\
    "  }\n"\
    "};\n"\
    "\n"\
    "/**\n"\
    " * Returns the root element of the node.  Found by traversing parentNodes until\n"\
    " * a node with no parent is found.  This node is considered the root.\n"\
    " * @param {!Node} node The node to find the root element for.\n"\
    " * @return {!Node} The root node.\n"\
    " */\n"\
    "function getNodeRoot(node) {\n"\
    "  while (node.parentNode) {\n"\
    "    node = node.parentNode;\n"\
    "  }\n"\
    "  return node;\n"\
    "}\n"\
    "\n"\
    "/**\n"\
    " * Returns the global object cache for the page.\n"\
    " * @param {Document=} opt_doc The document whose cache to retrieve. Defaults to\n"\
    " *     the current document.\n"\
    " * @return {!Cache} The page's object cache.\n"\
    " */\n"\
    "function getPageCache(opt_doc) {\n"\
    "  var doc = opt_doc || document;\n"\
    "  var key = '$cdc_asdjflasutopfhvcZLmcfl_';\n"\
    "  if (!(key in doc))\n"\
    "    doc[key] = new Cache();\n"\
    "  return doc[key];\n"\
    "}\n"\
    "\n"\
    "/**\n"\
    " * Wraps the given value to be transmitted remotely by converting\n"\
    " * appropriate objects to cached object IDs.\n"\
    " *\n"\
    " * @param {*} value The value to wrap.\n"\
    " * @return {*} The wrapped value.\n"\
    " */\n"\
    "function wrap(value) {\n"\
    "  if (typeof(value) == 'object' && value != null) {\n"\
    "    var nodeType = value['nodeType'];\n"\
    "    if (nodeType == NodeType.ELEMENT || nodeType == NodeType.DOCUMENT\n"\
    "        || (SHADOW_DOM_ENABLED && value instanceof WebKitShadowRoot)) {\n"\
    "      var wrapped = {};\n"\
    "      var root = getNodeRoot(value);\n"\
    "      wrapped[ELEMENT_KEY] = getPageCache(root).storeItem(value);\n"\
    "      return wrapped;\n"\
    "    }\n"\
    "\n"\
    "    var obj = (typeof(value.length) == 'number') ? [] : {};\n"\
    "    for (var prop in value)\n"\
    "      obj[prop] = wrap(value[prop]);\n"\
    "    return obj;\n"\
    "  }\n"\
    "  return value;\n"\
    "}\n"\
    "\n"\
    "/**\n"\
    " * Unwraps the given value by converting from object IDs to the cached\n"\
    " * objects.\n"\
    " *\n"\
    " * @param {*} value The value to unwrap.\n"\
    " * @param {Cache} cache The cache to retrieve wrapped elements from.\n"\
    " * @return {*} The unwrapped value.\n"\
    " */\n"\
    "function unwrap(value, cache) {\n"\
    "  if (typeof(value) == 'object' && value != null) {\n"\
    "    if (ELEMENT_KEY in value)\n"\
    "      return cache.retrieveItem(value[ELEMENT_KEY]);\n"\
    "\n"\
    "    var obj = (typeof(value.length) == 'number') ? [] : {};\n"\
    "    for (var prop in value)\n"\
    "      obj[prop] = unwrap(value[prop], cache);\n"\
    "    return obj;\n"\
    "  }\n"\
    "  return value;\n"\
    "}\n"\
    "\n"\
    "/**\n"\
    " * Calls a given function and returns its value.\n"\
    " *\n"\
    " * The inputs to and outputs of the function will be unwrapped and wrapped\n"\
    " * respectively, unless otherwise specified. This wrapping involves converting\n"\
    " * between cached object reference IDs and actual JS objects. The cache will\n"\
    " * automatically be pruned each call to remove stale references.\n"\
    " *\n"\
    " * @param  {Array.<string>} shadowHostIds The host ids of the nested shadow\n"\
    " *     DOMs the function should be executed in the context of.\n"\
    " * @param {function(...[*]) : *} func The function to invoke.\n"\
    " * @param {!Array.<*>} args The array of arguments to supply to the function,\n"\
    " *     which will be unwrapped before invoking the function.\n"\
    " * @param {boolean=} opt_unwrappedReturn Whether the function's return value\n"\
    " *     should be left unwrapped.\n"\
    " * @return {*} An object containing a status and value property, where status\n"\
    " *     is a WebDriver status code and value is the wrapped value. If an\n"\
    " *     unwrapped return was specified, this will be the function's pure return\n"\
    " *     value.\n"\
    " */\n"\
    "function callFunction(shadowHostIds, func, args, opt_unwrappedReturn) {\n"\
    "  var cache = getPageCache();\n"\
    "  cache.clearStale();\n"\
    "  if (shadowHostIds && SHADOW_DOM_ENABLED) {\n"\
    "    for (var i = 0; i < shadowHostIds.length; i++) {\n"\
    "      var host = cache.retrieveItem(shadowHostIds[i]);\n"\
    "      // TODO(wyh): Use the olderShadowRoot API when available to check\n"\
    "      // all of the shadow roots.\n"\
    "      cache = getPageCache(host.webkitShadowRoot);\n"\
    "      cache.clearStale();\n"\
    "    }\n"\
    "  }\n"\
    "\n"\
    "  if (opt_unwrappedReturn)\n"\
    "    return func.apply(null, unwrap(args, cache));\n"\
    "\n"\
    "  var status = 0;\n"\
    "  try {\n"\
    "    var returnValue = wrap(func.apply(null, unwrap(args, cache)));\n"\
    "  } catch (error) {\n"\
    "    status = error.code || StatusCode.UNKNOWN_ERROR;\n"\
    "    var returnValue = error.message;\n"\
    "  }\n"\
    "  return {\n"\
    "      status: status,\n"\
    "      value: returnValue\n"\
    "  }\n"\
    "}\n"\
    "; return callFunction.apply(null, arguments) }\n"
kDispatchContextMenuEventScript =\
    "function() { // Copyright Modify to our own signature. All rights reserved.\n"\
    "// Use of this source code is governed by a BSD-style license that can be\n"\
    "// found in the LICENSE file.\n"\
    "\n"\
    "/**\n"\
    " * Enum for modifier keys, same as DevTools protocol.\n"\
    " * @enum {number}\n"\
    " */\n"\
    "var ModifierMask = {\n"\
    "  ALT: 1 << 0,\n"\
    "  CTRL: 1 << 1,\n"\
    "  META: 1 << 2,\n"\
    "  SHIFT: 1 << 3,\n"\
    "};\n"\
    "\n"\
    "/**\n"\
    " * Dispatches a context menu event at the given location.\n"\
    " *\n"\
    " * @param {number} x The X coordinate to dispatch the event at.\n"\
    " * @param {number} y The Y coordinate to dispatch the event at.\n"\
    " * @param {modifiers} modifiers The modifiers to use for the event.\n"\
    " */\n"\
    "function dispatchContextMenuEvent(x, y, modifiers) {\n"\
    "  var event = new MouseEvent(\n"\
    "      'contextmenu',\n"\
    "      {view: window,\n"\
    "       bubbles: true,\n"\
    "       cancelable: true,\n"\
    "       screenX: x,\n"\
    "       screenY: y,\n"\
    "       clientX: x,\n"\
    "       clientY: y,\n"\
    "       ctrlKey: modifiers & ModifierMask.CTRL,\n"\
    "       altKey: modifiers & ModifierMask.ALT,\n"\
    "       shiftKey: modifiers & ModifierMask.SHIFT,\n"\
    "       metaKey: modifiers & ModifierMask.META,\n"\
    "       button: 2});\n"\
    "\n"\
    "  var elem = document.elementFromPoint(x, y);\n"\
    "  if (!elem) {\n"\
    "    throw new Error('cannot right click outside the visible bounds of the ' +\n"\
    "                    'document: (' + x + ', ' + y + ')');\n"\
    "  }\n"\
    "  elem.dispatchEvent(event);\n"\
    "}\n"\
    "; return dispatchContextMenuEvent.apply(null, arguments) }\n"

if __name__ == "__main__":
  print kFocusScript
  print kGetElementRegionScript
  print kIsOptionElementToggleableScript
  print kExecuteAsyncScriptScript
  print kAddCookieScript
  print kCallFunctionScript
  print kDispatchContextMenuEventScript

