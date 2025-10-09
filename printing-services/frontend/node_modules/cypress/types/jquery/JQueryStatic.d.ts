// tslint:disable:jsdoc-format
// tslint:disable:max-line-length
// tslint:disable:no-irregular-whitespace

interface JQueryStatic {
    /**
     * @see \`{@link https://api.jquery.com/jquery.ajax/#jQuery-ajax1 }\`
     * @deprecated ​ Deprecated. Use \`{@link ajaxSetup }\`.
     */
    ajaxSettings: JQuery.AjaxSettings;
    Animation: JQuery.AnimationStatic;
    Callbacks: JQuery.CallbacksStatic;
    /**
     * Hook directly into jQuery to override how particular CSS properties are retrieved or set, normalize CSS property naming, or create custom properties.
     * @see \`{@link https://api.jquery.com/jQuery.cssHooks/ }\`
     * @since 1.4.3
     */
    cssHooks: JQuery.CSSHooks;
    /**
     * An object containing all CSS properties that may be used without a unit. The .css() method uses this object to see if it may append px to unitless values.
     * @see \`{@link https://api.jquery.com/jQuery.cssNumber/ }\`
     * @since 1.4.3
     */
    cssNumber: JQuery.PlainObject<boolean>;
    Deferred: JQuery.DeferredStatic;
    easing: JQuery.Easings;
    Event: JQuery.EventStatic;
    /**
     * @see \`{@link https://learn.jquery.com/events/event-extensions/ }\`
     */
    event: JQuery.EventExtensions;
    expr: JQuery.Selectors;
    // Set to HTMLElement to minimize breaks but should probably be Element.
    readonly fn: JQuery;
    fx: JQuery.Effects;
    /**
     * A Promise-like object (or "thenable") that resolves when the document is ready.
     * @see \`{@link https://api.jquery.com/jQuery.ready/ }\`
     * @since 1.8
     * @example ​ ````Listen for document ready using jQuery.when.
```javascript
$.when( $.ready ).then(function() {
  // Document is ready.
});
```
     * @example ​ ````Typical usage involving another promise, using jQuery.when.
```javascript
$.when(
  $.getJSON( "ajax/test.json" ),
  $.ready
).done(function( data ) {
  // Document is ready.
  // Value of test.json is passed as `data`.
});
```
     */
    ready: JQuery.Thenable<JQueryStatic>;
    /**
     * A collection of properties that represent the presence of different browser features or bugs. Intended for jQuery's internal use; specific properties may be removed when they are no longer needed internally to improve page startup performance. For your own project's feature-detection needs, we strongly recommend the use of an external library such as Modernizr instead of dependency on properties in jQuery.support.
     * @see \`{@link https://api.jquery.com/jQuery.support/ }\`
     * @since 1.3
     * @deprecated ​ Deprecated since 1.9. See \`{@link https://api.jquery.com/jQuery.support/ }\`.
     */
    support: JQuery.PlainObject;
    timers: Array<JQuery.TickFunction<any>>;
    Tween: JQuery.TweenStatic;
    valHooks: JQuery.ValHooks;
    // HACK: This is the factory function returned when importing jQuery without a DOM. Declaring it separately breaks using the type parameter on JQueryStatic.
    // HACK: The discriminator parameter handles the edge case of passing a Window object to JQueryStatic. It doesn't actually exist on the factory function.
    (window: Window, discriminator: boolean): JQueryStatic;
    /**
     * Creates DOM elements on the fly from the provided string of raw HTML.
     * @param html _&#x40;param_ `html`
     * <br>
     * * `html (ownerDocument)` — A string of HTML to create on the fly. Note that this parses HTML, not XML. <br>
     * * `html (attributes)` — A string defining a single, standalone, HTML element (e.g. &lt;div/&gt; or &lt;div&gt;&lt;/div&gt;).
     * @param ownerDocument_attributes _&#x40;param_ `ownerDocument_attributes`
     * <br>
     * * `ownerDocument` — A document in which the new elements will be created. <br>
     * * `attributes` — An object of attributes, events, and methods to call on the newly-created element.
     * @see \`{@link https://api.jquery.com/jQuery/ }\`
     * @since 1.0
     * @since 1.4
     * @example ​ ````Create a div element (and all of its contents) dynamically and append it to the body element. Internally, an element is created and its innerHTML property set to the given markup.
```javascript
$( "<div><p>Hello</p></div>" ).appendTo( "body" )
```
     * @example ​ ````Create some DOM elements.
```javascript
$( "<div/>", {
  "class": "test",
  text: "Click me!",
  click: function() {
    $( this ).toggleClass( "test" );
  }
})
  .appendTo( "body" );
```
     */
    // tslint:disable-next-line:no-unnecessary-generics
    <TElement extends HTMLElement = HTMLElement>(html: JQuery.htmlString, ownerDocument_attributes?: Document | JQuery.PlainObject): JQuery<TElement>;
    /**
     * Accepts a string containing a CSS selector which is then used to match a set of elements.
     * @param selector A string containing a selector expression
     * @param context A DOM Element, Document, or jQuery to use as context
     * @see \`{@link https://api.jquery.com/jQuery/ }\`
     * @since 1.0
     * @example ​ ````Find all p elements that are children of a div element and apply a border to them.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p>one</p>
<div><p>two</p></div>
<p>three</p>
​
<script>
$( "div > p" ).css( "border", "1px solid gray" );
</script>
</body>
</html>
```
     * @example ​ ````Find all inputs of type radio within the first form in the document.
```javascript
$( "input:radio", document.forms[ 0 ] );
```
     * @example ​ ````Find all div elements within an XML document from an Ajax response.
```javascript
$( "div", xml.responseXML );
```
​
     */
    // tslint:disable-next-line:no-unnecessary-generics
    <TElement extends Element = HTMLElement>(selector: JQuery.Selector, context?: Element | Document | JQuery): JQuery<TElement>;
    /**
     * Return a collection of matched elements either found in the DOM based on passed argument(s) or created by passing an HTML string.
     * @param element A DOM element to wrap in a jQuery object.
     * @see \`{@link https://api.jquery.com/jQuery/ }\`
     * @since 1.0
     * @example ​ ````Set the background color of the page to black.
```javascript
$( document.body ).css( "background", "black" );
```
     */
    // NOTE: `HTMLSelectElement` is both an Element and an Array-Like Object but jQuery treats it as an Element.
    (element: HTMLSelectElement): JQuery<HTMLSelectElement>;
    /**
     * Return a collection of matched elements either found in the DOM based on passed argument(s) or created by passing an HTML string.
     * @param element_elementArray _&#x40;param_ `element_elementArray`
     * <br>
     * * `element` — A DOM element to wrap in a jQuery object. <br>
     * * `elementArray` — An array containing a set of DOM elements to wrap in a jQuery object.
     * @see \`{@link https://api.jquery.com/jQuery/ }\`
     * @since 1.0
     * @example ​ ````Set the background color of the page to black.
```javascript
$( document.body ).css( "background", "black" );
```
     * @example ​ ````Hide all the input elements within a form.
```javascript
$( myForm.elements ).hide();
```
     */
    <T extends Element>(element_elementArray: T | ArrayLike<T>): JQuery<T>;
    /**
     * Return a collection of matched elements either found in the DOM based on passed argument(s) or created by passing an HTML string.
     * @param selection An existing jQuery object to clone.
     * @see \`{@link https://api.jquery.com/jQuery/ }\`
     * @since 1.0
     */
    <T>(selection: JQuery<T>): JQuery<T>;
    /**
     * Binds a function to be executed when the DOM has finished loading.
     * @param callback The function to execute when the DOM is ready.
     * @see \`{@link https://api.jquery.com/jQuery/ }\`
     * @since 1.0
     * @example ​ ````Execute the function when the DOM is ready to be used.
```javascript
$(function() {
  // Document is ready
});
```
     * @example ​ ````Use both the shortcut for $(document).ready() and the argument to write failsafe jQuery code using the $ alias, without relying on the global alias.
```javascript
jQuery(function( $ ) {
  // Your code using failsafe $ alias here...
});
```
     */
    // tslint:disable-next-line:no-unnecessary-generics unified-signatures
    <TElement = HTMLElement>(callback: ((this: Document, $: JQueryStatic) => void)): JQuery<TElement>;
    /**
     * Return a collection of matched elements either found in the DOM based on passed argument(s) or created by passing an HTML string.
     * @param object A plain object to wrap in a jQuery object.
     * @see \`{@link https://api.jquery.com/jQuery/ }\`
     * @since 1.0
     */
    <T extends JQuery.PlainObject>(object: T): JQuery<T>;
    /**
     * Returns an empty jQuery set.
     * @see \`{@link https://api.jquery.com/jQuery/ }\`
     * @since 1.4
     */
    // tslint:disable-next-line:no-unnecessary-generics
    <TElement = HTMLElement>(): JQuery<TElement>;
    /**
     * Perform an asynchronous HTTP (Ajax) request.
     * @param url A string containing the URL to which the request is sent.
     * @param settings A set of key/value pairs that configure the Ajax request. All settings are optional. A default can
     *                 be set for any option with $.ajaxSetup(). See jQuery.ajax( settings ) below for a complete list of all settings.
     * @see \`{@link https://api.jquery.com/jQuery.ajax/ }\`
     * @since 1.5
     */
    ajax(url: string, settings?: JQuery.AjaxSettings): JQuery.jqXHR;
    /**
     * Perform an asynchronous HTTP (Ajax) request.
     * @param settings A set of key/value pairs that configure the Ajax request. All settings are optional. A default can
     *                 be set for any option with $.ajaxSetup().
     * @see \`{@link https://api.jquery.com/jQuery.ajax/ }\`
     * @since 1.0
     * @example ​ ````Save some data to the server and notify the user once it&#39;s complete.
```javascript
$.ajax({
  method: "POST",
  url: "some.php",
  data: { name: "John", location: "Boston" }
})
  .done(function( msg ) {
    alert( "Data Saved: " + msg );
  });
```
     * @example ​ ````Retrieve the latest version of an HTML page.
```javascript
$.ajax({
  url: "test.html",
  cache: false
})
  .done(function( html ) {
    $( "#results" ).append( html );
  });
```
     * @example ​ ````Send an xml document as data to the server. By setting the processData
    option to false, the automatic conversion of data to strings is prevented.
```javascript
var xmlDocument = [create xml document];
var xmlRequest = $.ajax({
  url: "page.php",
  processData: false,
  data: xmlDocument
});
​
xmlRequest.done( handleResponse );
```
     * @example ​ ````Send an id as data to the server, save some data to the server, and notify the user once it&#39;s complete. If the request fails, alert the user.
```javascript
var menuId = $( "ul.nav" ).first().attr( "id" );
var request = $.ajax({
  url: "script.php",
  method: "POST",
  data: { id : menuId },
  dataType: "html"
});
​
request.done(function( msg ) {
  $( "#log" ).html( msg );
});
​
request.fail(function( jqXHR, textStatus ) {
  alert( "Request failed: " + textStatus );
});
```
     * @example ​ ````Load and execute a JavaScript file.
```javascript
$.ajax({
  method: "GET",
  url: "test.js",
  dataType: "script"
});
```
     */
    ajax(settings?: JQuery.AjaxSettings): JQuery.jqXHR;
    /**
     * Handle custom Ajax options or modify existing options before each request is sent and before they are processed by $.ajax().
     * @param dataTypes An optional string containing one or more space-separated dataTypes
     * @param handler A handler to set default values for future Ajax requests.
     * @see \`{@link https://api.jquery.com/jQuery.ajaxPrefilter/ }\`
     * @since 1.5
     */
    ajaxPrefilter(dataTypes: string,
                  handler: (options: JQuery.AjaxSettings, originalOptions: JQuery.AjaxSettings, jqXHR: JQuery.jqXHR) => string | void): void;
    /**
     * Handle custom Ajax options or modify existing options before each request is sent and before they are processed by $.ajax().
     * @param handler A handler to set default values for future Ajax requests.
     * @see \`{@link https://api.jquery.com/jQuery.ajaxPrefilter/ }\`
     * @since 1.5
     */
    ajaxPrefilter(handler: (options: JQuery.AjaxSettings, originalOptions: JQuery.AjaxSettings, jqXHR: JQuery.jqXHR) => string | void): void;
    /**
     * Set default values for future Ajax requests. Its use is not recommended.
     * @param options A set of key/value pairs that configure the default Ajax request. All options are optional.
     * @see \`{@link https://api.jquery.com/jQuery.ajaxSetup/ }\`
     * @since 1.1
     * @example ​ ````Sets the defaults for Ajax requests to the url &quot;/xmlhttp/&quot;, disables global handlers and uses POST instead of GET. The following Ajax requests then sends some data without having to set anything else.
```javascript
$.ajaxSetup({
  url: "/xmlhttp/",
  global: false,
  type: "POST"
});
$.ajax({ data: myData });
```
     */
    ajaxSetup(options: JQuery.AjaxSettings): JQuery.AjaxSettings;
    /**
     * Creates an object that handles the actual transmission of Ajax data.
     * @param dataType A string identifying the data type to use
     * @param handler A handler to return the new transport object to use with the data type provided in the first argument.
     * @see \`{@link https://api.jquery.com/jQuery.ajaxTransport/ }\`
     * @since 1.5
     */
    ajaxTransport(dataType: string,
                  handler: (options: JQuery.AjaxSettings, originalOptions: JQuery.AjaxSettings, jqXHR: JQuery.jqXHR) => JQuery.Transport | void): void;
    /**
     * @deprecated ​ Deprecated since 3.3. Internal. See \`{@link https://github.com/jquery/jquery/issues/3384 }\`.
     */
    camelCase(value: string): string;
    cleanData(elems: ArrayLike<Element | Document | Window | JQuery.PlainObject>): void;
    /**
     * Check to see if a DOM element is a descendant of another DOM element.
     * @param container The DOM element that may contain the other element.
     * @param contained The DOM element that may be contained by (a descendant of) the other element.
     * @see \`{@link https://api.jquery.com/jQuery.contains/ }\`
     * @since 1.4
     * @example ​ ````Check if an element is a descendant of another.
```javascript
$.contains( document.documentElement, document.body ); // true
$.contains( document.body, document.documentElement ); // false
```
     */
    contains(container: Element, contained: Element): boolean;
    css(elem: Element, name: string): any;
    /**
     * Store arbitrary data associated with the specified element. Returns the value that was set.
     * @param element The DOM element to associate with the data.
     * @param key A string naming the piece of data to set.
     * @param value The new data value; this can be any Javascript type except `undefined`.
     * @see \`{@link https://api.jquery.com/jQuery.data/ }\`
     * @since 1.2.3
     * @example ​ ````Get the data named &quot;blah&quot; stored at for an element.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.data demo</title>
  <style>
  div {
    margin: 5px;
    background: yellow;
  }
  button {
    margin: 5px;
    font-size: 14px;
  }
  p {
    margin: 5px;
    color: blue;
  }
  span {
    color: red;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<div>A div</div>
<button>Get "blah" from the div</button>
<button>Set "blah" to "hello"</button>
<button>Set "blah" to 86</button>
<button>Remove "blah" from the div</button>
<p>The "blah" value of this div is <span>?</span></p>
​
<script>
$( "button" ).click( function() {
  var value,
    div = $( "div" )[ 0 ];
  switch ( $( "button" ).index( this ) ) {
  case 0 :
    value = jQuery.data( div, "blah" );
    break;
  case 1 :
    jQuery.data( div, "blah", "hello" );
    value = "Stored!";
    break;
  case 2 :
    jQuery.data( div, "blah", 86 );
    value = "Stored!";
    break;
  case 3 :
    jQuery.removeData( div, "blah" );
    value = "Removed!";
    break;
  }
  $( "span" ).text( "" + value );
});
</script>
​
</body>
</html>
```
     */
    data<T extends string | number | boolean | symbol | object | null>(element: Element | Document | Window | JQuery.PlainObject, key: string, value: T): T;
    /**
     * Returns value at named data store for the element, as set by `jQuery.data(element, name, value)`, or the full data store for the element.
     * @param element The DOM element to query for the data.
     * @param key Name of the data stored.
     * @param value `undefined` is not recognized as a data value. Calls such as `jQuery.data( el, "name", undefined )`
     *              will return the corresponding data for "name", and is therefore the same as `jQuery.data( el, "name" )`
     * @see \`{@link https://api.jquery.com/jQuery.data/ }\`
     * @since 1.2.3
     */
    // `unified-signatures` is disabled so that behavior when passing `undefined` to `value` can be documented. Unifying the signatures
    // results in potential confusion for users from an unexpected parameter.
    // tslint:disable-next-line:unified-signatures
    data(element: Element | Document | Window | JQuery.PlainObject, key: string, value: undefined): any;
    /**
     * Returns value at named data store for the element, as set by `jQuery.data(element, name, value)`, or the full data store for the element.
     * @param element The DOM element to query for the data.
     * @param key Name of the data stored.
     * @see \`{@link https://api.jquery.com/jQuery.data/ }\`
     * @since 1.2.3
     * @since 1.4
     * @example ​ ````Store then retrieve a value from the div element.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.data demo</title>
  <style>
  div {
    color: blue;
  }
  span {
    color: red;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<div>
  The values stored were
  <span></span>
  and
  <span></span>
</div>
​
<script>
var div = $( "div" )[ 0 ];
jQuery.data( div, "test", {
  first: 16,
  last: "pizza!"
});
$( "span:first" ).text( jQuery.data( div, "test" ).first );
$( "span:last" ).text( jQuery.data( div, "test" ).last );
</script>
​
</body>
</html>
```
     */
    data(element: Element | Document | Window | JQuery.PlainObject, key?: string): any;
    /**
     * Execute the next function on the queue for the matched element.
     * @param element A DOM element from which to remove and execute a queued function.
     * @param queueName A string containing the name of the queue. Defaults to fx, the standard effects queue.
     * @see \`{@link https://api.jquery.com/jQuery.dequeue/ }\`
     * @since 1.3
     * @example ​ ````Use jQuery.dequeue() to end a custom queue function which allows the queue to keep going.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.dequeue demo</title>
  <style>
  div {
    margin: 3px;
    width: 50px;
    position: absolute;
    height: 50px;
    left: 10px;
    top: 30px;
    background-color: yellow;
  }
  div.red {
    background-color: red;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<button>Start</button>
<div></div>
​
<script>
$( "button" ).click(function() {
  $( "div" )
    .animate({ left: '+=200px' }, 2000 )
    .animate({ top: '0px' }, 600 )
    .queue(function() {
      $( this ).toggleClass( "red" );
      $.dequeue( this );
    })
    .animate({ left:'10px', top:'30px' }, 700 );
});
</script>
​
</body>
</html>
```
     */
    dequeue(element: Element, queueName?: string): void;
    /**
     * A generic iterator function, which can be used to seamlessly iterate over both objects and arrays. Arrays and array-like objects with a length property (such as a function's arguments object) are iterated by numeric index, from 0 to length-1. Other objects are iterated via their named properties.
     * @param array The array to iterate over.
     * @param callback The function that will be executed on every object.
     * @see \`{@link https://api.jquery.com/jQuery.each/ }\`
     * @since 1.0
     * @example ​ ````Iterates through the array displaying each number as both a word and numeral
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.each demo</title>
  <style>
  div {
    color: blue;
  }
  div#five {
    color: red;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<div id="one"></div>
<div id="two"></div>
<div id="three"></div>
<div id="four"></div>
<div id="five"></div>
​
<script>
var arr = [ "one", "two", "three", "four", "five" ];
var obj = { one: 1, two: 2, three: 3, four: 4, five: 5 };
​
jQuery.each( arr, function( i, val ) {
  $( "#" + val ).text( "Mine is " + val + "." );
​
  // Will stop running after "three"
  return ( val !== "three" );
});
​
jQuery.each( obj, function( i, val ) {
  $( "#" + i ).append( document.createTextNode( " - " + val ) );
});
</script>
​
</body>
</html>
```
     * @example ​ ````Iterates over items in an array, accessing both the current item and its index.
```javascript
$.each( [ "a", "b", "c" ], function( i, l ){
  alert( "Index #" + i + ": " + l );
});
```
     */
    each<T>(array: ArrayLike<T>, callback: (this: T, indexInArray: number, value: T) => any): ArrayLike<T>;
    /**
     * A generic iterator function, which can be used to seamlessly iterate over both objects and arrays. Arrays and array-like objects with a length property (such as a function's arguments object) are iterated by numeric index, from 0 to length-1. Other objects are iterated via their named properties.
     * @param obj The object to iterate over.
     * @param callback The function that will be executed on every object.
     * @see \`{@link https://api.jquery.com/jQuery.each/ }\`
     * @since 1.0
     * @example ​ ````Iterates through the array displaying each number as both a word and numeral
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.each demo</title>
  <style>
  div {
    color: blue;
  }
  div#five {
    color: red;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<div id="one"></div>
<div id="two"></div>
<div id="three"></div>
<div id="four"></div>
<div id="five"></div>
​
<script>
var arr = [ "one", "two", "three", "four", "five" ];
var obj = { one: 1, two: 2, three: 3, four: 4, five: 5 };
​
jQuery.each( arr, function( i, val ) {
  $( "#" + val ).text( "Mine is " + val + "." );
​
  // Will stop running after "three"
  return ( val !== "three" );
});
​
jQuery.each( obj, function( i, val ) {
  $( "#" + i ).append( document.createTextNode( " - " + val ) );
});
</script>
​
</body>
</html>
```
     * @example ​ ````Iterates over the properties in an object, accessing both the current item and its key.
```javascript
$.each({ name: "John", lang: "JS" }, function( k, v ) {
  alert( "Key: " + k + ", Value: " + v );
});
```
     */
    each<T, K extends keyof T>(obj: T, callback: (this: T[K], propertyName: K, valueOfProperty: T[K]) => any): T;
    /**
     * Takes a string and throws an exception containing it.
     * @param message The message to send out.
     * @see \`{@link https://api.jquery.com/jQuery.error/ }\`
     * @since 1.4.1
     * @example ​ ````Override jQuery.error for display in Firebug.
```javascript
jQuery.error = console.error;
```
     */
    error(message: string): any;
    /**
     * Escapes any character that has a special meaning in a CSS selector.
     * @param selector A string containing a selector expression to escape.
     * @see \`{@link https://api.jquery.com/jQuery.escapeSelector/ }\`
     * @since 3.0
     * @example ​ ````Escape an ID containing a hash.
```javascript
$.escapeSelector( "#target" ); // "\#target"
```
     * @example ​ ````Select all the elements having a class name of .box inside a div.
```javascript
$( "div" ).find( "." + $.escapeSelector( ".box" ) );
```
     */
    escapeSelector(selector: JQuery.Selector): JQuery.Selector;
    /**
     * Merge the contents of two or more objects together into the first object.
     * @param deep If true, the merge becomes recursive (aka. deep copy). Passing false for this argument is not supported.
     * @param target The object to extend. It will receive the new properties.
     * @param object1 An object containing additional properties to merge in.
     * @param object2 An object containing additional properties to merge in.
     * @param object3 An object containing additional properties to merge in.
     * @param object4 An object containing additional properties to merge in.
     * @param object5 An object containing additional properties to merge in.
     * @param object6 An object containing additional properties to merge in.
     * @see \`{@link https://api.jquery.com/jQuery.extend/ }\`
     * @since 1.1.4
     * @example ​ ````Merge two objects recursively, modifying the first.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.extend demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<div id="log"></div>
​
<script>
var object1 = {
  apple: 0,
  banana: { weight: 52, price: 100 },
  cherry: 97
};
var object2 = {
  banana: { price: 200 },
  durian: 100
};
​
// Merge object2 into object1, recursively
$.extend( true, object1, object2 );
​
// Assuming JSON.stringify - not available in IE<8
$( "#log" ).append( JSON.stringify( object1 ) );
</script>
​
</body>
</html>
```
     */
    extend<T, U, V, W, X, Y, Z>(deep: true, target: T, object1: U, object2: V, object3: W, object4: X, object5: Y, object6: Z): T & U & V & W & X & Y & Z;
    /**
     * Merge the contents of two or more objects together into the first object.
     * @param deep If true, the merge becomes recursive (aka. deep copy). Passing false for this argument is not supported.
     * @param target The object to extend. It will receive the new properties.
     * @param object1 An object containing additional properties to merge in.
     * @param object2 An object containing additional properties to merge in.
     * @param object3 An object containing additional properties to merge in.
     * @param object4 An object containing additional properties to merge in.
     * @param object5 An object containing additional properties to merge in.
     * @see \`{@link https://api.jquery.com/jQuery.extend/ }\`
     * @since 1.1.4
     * @example ​ ````Merge two objects recursively, modifying the first.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.extend demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<div id="log"></div>
​
<script>
var object1 = {
  apple: 0,
  banana: { weight: 52, price: 100 },
  cherry: 97
};
var object2 = {
  banana: { price: 200 },
  durian: 100
};
​
// Merge object2 into object1, recursively
$.extend( true, object1, object2 );
​
// Assuming JSON.stringify - not available in IE<8
$( "#log" ).append( JSON.stringify( object1 ) );
</script>
​
</body>
</html>
```
     */
    extend<T, U, V, W, X, Y>(deep: true, target: T, object1: U, object2: V, object3: W, object4: X, object5: Y): T & U & V & W & X & Y;
    /**
     * Merge the contents of two or more objects together into the first object.
     * @param deep If true, the merge becomes recursive (aka. deep copy). Passing false for this argument is not supported.
     * @param target The object to extend. It will receive the new properties.
     * @param object1 An object containing additional properties to merge in.
     * @param object2 An object containing additional properties to merge in.
     * @param object3 An object containing additional properties to merge in.
     * @param object4 An object containing additional properties to merge in.
     * @see \`{@link https://api.jquery.com/jQuery.extend/ }\`
     * @since 1.1.4
     * @example ​ ````Merge two objects recursively, modifying the first.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.extend demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<div id="log"></div>
​
<script>
var object1 = {
  apple: 0,
  banana: { weight: 52, price: 100 },
  cherry: 97
};
var object2 = {
  banana: { price: 200 },
  durian: 100
};
​
// Merge object2 into object1, recursively
$.extend( true, object1, object2 );
​
// Assuming JSON.stringify - not available in IE<8
$( "#log" ).append( JSON.stringify( object1 ) );
</script>
​
</body>
</html>
```
     */
    extend<T, U, V, W, X>(deep: true, target: T, object1: U, object2: V, object3: W, object4: X): T & U & V & W & X;
    /**
     * Merge the contents of two or more objects together into the first object.
     * @param deep If true, the merge becomes recursive (aka. deep copy). Passing false for this argument is not supported.
     * @param target The object to extend. It will receive the new properties.
     * @param object1 An object containing additional properties to merge in.
     * @param object2 An object containing additional properties to merge in.
     * @param object3 An object containing additional properties to merge in.
     * @see \`{@link https://api.jquery.com/jQuery.extend/ }\`
     * @since 1.1.4
     * @example ​ ````Merge two objects recursively, modifying the first.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.extend demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<div id="log"></div>
​
<script>
var object1 = {
  apple: 0,
  banana: { weight: 52, price: 100 },
  cherry: 97
};
var object2 = {
  banana: { price: 200 },
  durian: 100
};
​
// Merge object2 into object1, recursively
$.extend( true, object1, object2 );
​
// Assuming JSON.stringify - not available in IE<8
$( "#log" ).append( JSON.stringify( object1 ) );
</script>
​
</body>
</html>
```
     */
    extend<T, U, V, W>(deep: true, target: T, object1: U, object2: V, object3: W): T & U & V & W;
    /**
     * Merge the contents of two or more objects together into the first object.
     * @param deep If true, the merge becomes recursive (aka. deep copy). Passing false for this argument is not supported.
     * @param target The object to extend. It will receive the new properties.
     * @param object1 An object containing additional properties to merge in.
     * @param object2 An object containing additional properties to merge in.
     * @see \`{@link https://api.jquery.com/jQuery.extend/ }\`
     * @since 1.1.4
     * @example ​ ````Merge two objects recursively, modifying the first.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.extend demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<div id="log"></div>
​
<script>
var object1 = {
  apple: 0,
  banana: { weight: 52, price: 100 },
  cherry: 97
};
var object2 = {
  banana: { price: 200 },
  durian: 100
};
​
// Merge object2 into object1, recursively
$.extend( true, object1, object2 );
​
// Assuming JSON.stringify - not available in IE<8
$( "#log" ).append( JSON.stringify( object1 ) );
</script>
​
</body>
</html>
```
     */
    extend<T, U, V>(deep: true, target: T, object1: U, object2: V): T & U & V;
    /**
     * Merge the contents of two or more objects together into the first object.
     * @param deep If true, the merge becomes recursive (aka. deep copy). Passing false for this argument is not supported.
     * @param target The object to extend. It will receive the new properties.
     * @param object1 An object containing additional properties to merge in.
     * @see \`{@link https://api.jquery.com/jQuery.extend/ }\`
     * @since 1.1.4
     * @example ​ ````Merge two objects recursively, modifying the first.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.extend demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<div id="log"></div>
​
<script>
var object1 = {
  apple: 0,
  banana: { weight: 52, price: 100 },
  cherry: 97
};
var object2 = {
  banana: { price: 200 },
  durian: 100
};
​
// Merge object2 into object1, recursively
$.extend( true, object1, object2 );
​
// Assuming JSON.stringify - not available in IE<8
$( "#log" ).append( JSON.stringify( object1 ) );
</script>
​
</body>
</html>
```
     */
    extend<T, U>(deep: true, target: T, object1: U): T & U;
    /**
     * Merge the contents of two or more objects together into the first object.
     * @param deep If true, the merge becomes recursive (aka. deep copy). Passing false for this argument is not supported.
     * @param target The object to extend. It will receive the new properties.
     * @see \`{@link https://api.jquery.com/jQuery.extend/ }\`
     * @since 1.1.4
     */
    extend<T>(deep: true, target: T): this & T;
    /**
     * Merge the contents of two or more objects together into the first object.
     * @param deep If true, the merge becomes recursive (aka. deep copy). Passing false for this argument is not supported.
     * @param target The object to extend. It will receive the new properties.
     * @param object1 An object containing additional properties to merge in.
     * @param objectN Additional objects containing properties to merge in.
     * @see \`{@link https://api.jquery.com/jQuery.extend/ }\`
     * @since 1.1.4
     * @example ​ ````Merge two objects recursively, modifying the first.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.extend demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<div id="log"></div>
​
<script>
var object1 = {
  apple: 0,
  banana: { weight: 52, price: 100 },
  cherry: 97
};
var object2 = {
  banana: { price: 200 },
  durian: 100
};
​
// Merge object2 into object1, recursively
$.extend( true, object1, object2 );
​
// Assuming JSON.stringify - not available in IE<8
$( "#log" ).append( JSON.stringify( object1 ) );
</script>
​
</body>
</html>
```
     */
    extend(deep: true, target: any, object1: any, ...objectN: any[]): any;
    /**
     * Merge the contents of two or more objects together into the first object.
     * @param target An object that will receive the new properties if additional objects are passed in or that will
     *               extend the jQuery namespace if it is the sole argument.
     * @param object1 An object containing additional properties to merge in.
     * @param object2 An object containing additional properties to merge in.
     * @param object3 An object containing additional properties to merge in.
     * @param object4 An object containing additional properties to merge in.
     * @param object5 An object containing additional properties to merge in.
     * @param object6 An object containing additional properties to merge in.
     * @see \`{@link https://api.jquery.com/jQuery.extend/ }\`
     * @since 1.0
     * @example ​ ````Merge two objects, modifying the first.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.extend demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<div id="log"></div>
​
<script>
var object1 = {
  apple: 0,
  banana: { weight: 52, price: 100 },
  cherry: 97
};
var object2 = {
  banana: { price: 200 },
  durian: 100
};
​
// Merge object2 into object1
$.extend( object1, object2 );
​
// Assuming JSON.stringify - not available in IE<8
$( "#log" ).append( JSON.stringify( object1 ) );
</script>
​
</body>
</html>
```
     * @example ​ ````Merge defaults and options, without modifying the defaults. This is a common plugin development pattern.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.extend demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<div id="log"></div>
​
<script>
var defaults = { validate: false, limit: 5, name: "foo" };
var options = { validate: true, name: "bar" };
​
// Merge defaults and options, without modifying defaults
var settings = $.extend( {}, defaults, options );
​
// Assuming JSON.stringify - not available in IE<8
$( "#log" ).append( "<div><b>defaults -- </b>" + JSON.stringify( defaults ) + "</div>" );
$( "#log" ).append( "<div><b>options -- </b>" + JSON.stringify( options ) + "</div>" );
$( "#log" ).append( "<div><b>settings -- </b>" + JSON.stringify( settings ) + "</div>" );
</script>
​
</body>
</html>
```
     */
    extend<T, U, V, W, X, Y, Z>(target: T, object1: U, object2: V, object3: W, object4: X, object5: Y, object6: Z): T & U & V & W & X & Y & Z;
    /**
     * Merge the contents of two or more objects together into the first object.
     * @param target An object that will receive the new properties if additional objects are passed in or that will
     *               extend the jQuery namespace if it is the sole argument.
     * @param object1 An object containing additional properties to merge in.
     * @param object2 An object containing additional properties to merge in.
     * @param object3 An object containing additional properties to merge in.
     * @param object4 An object containing additional properties to merge in.
     * @param object5 An object containing additional properties to merge in.
     * @see \`{@link https://api.jquery.com/jQuery.extend/ }\`
     * @since 1.0
     * @example ​ ````Merge two objects, modifying the first.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.extend demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<div id="log"></div>
​
<script>
var object1 = {
  apple: 0,
  banana: { weight: 52, price: 100 },
  cherry: 97
};
var object2 = {
  banana: { price: 200 },
  durian: 100
};
​
// Merge object2 into object1
$.extend( object1, object2 );
​
// Assuming JSON.stringify - not available in IE<8
$( "#log" ).append( JSON.stringify( object1 ) );
</script>
​
</body>
</html>
```
     * @example ​ ````Merge defaults and options, without modifying the defaults. This is a common plugin development pattern.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.extend demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<div id="log"></div>
​
<script>
var defaults = { validate: false, limit: 5, name: "foo" };
var options = { validate: true, name: "bar" };
​
// Merge defaults and options, without modifying defaults
var settings = $.extend( {}, defaults, options );
​
// Assuming JSON.stringify - not available in IE<8
$( "#log" ).append( "<div><b>defaults -- </b>" + JSON.stringify( defaults ) + "</div>" );
$( "#log" ).append( "<div><b>options -- </b>" + JSON.stringify( options ) + "</div>" );
$( "#log" ).append( "<div><b>settings -- </b>" + JSON.stringify( settings ) + "</div>" );
</script>
​
</body>
</html>
```
     */
    extend<T, U, V, W, X, Y>(target: T, object1: U, object2: V, object3: W, object4: X, object5: Y): T & U & V & W & X & Y;
    /**
     * Merge the contents of two or more objects together into the first object.
     * @param target An object that will receive the new properties if additional objects are passed in or that will
     *               extend the jQuery namespace if it is the sole argument.
     * @param object1 An object containing additional properties to merge in.
     * @param object2 An object containing additional properties to merge in.
     * @param object3 An object containing additional properties to merge in.
     * @param object4 An object containing additional properties to merge in.
     * @see \`{@link https://api.jquery.com/jQuery.extend/ }\`
     * @since 1.0
     * @example ​ ````Merge two objects, modifying the first.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.extend demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<div id="log"></div>
​
<script>
var object1 = {
  apple: 0,
  banana: { weight: 52, price: 100 },
  cherry: 97
};
var object2 = {
  banana: { price: 200 },
  durian: 100
};
​
// Merge object2 into object1
$.extend( object1, object2 );
​
// Assuming JSON.stringify - not available in IE<8
$( "#log" ).append( JSON.stringify( object1 ) );
</script>
​
</body>
</html>
```
     * @example ​ ````Merge defaults and options, without modifying the defaults. This is a common plugin development pattern.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.extend demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<div id="log"></div>
​
<script>
var defaults = { validate: false, limit: 5, name: "foo" };
var options = { validate: true, name: "bar" };
​
// Merge defaults and options, without modifying defaults
var settings = $.extend( {}, defaults, options );
​
// Assuming JSON.stringify - not available in IE<8
$( "#log" ).append( "<div><b>defaults -- </b>" + JSON.stringify( defaults ) + "</div>" );
$( "#log" ).append( "<div><b>options -- </b>" + JSON.stringify( options ) + "</div>" );
$( "#log" ).append( "<div><b>settings -- </b>" + JSON.stringify( settings ) + "</div>" );
</script>
​
</body>
</html>
```
     */
    extend<T, U, V, W, X>(target: T, object1: U, object2: V, object3: W, object4: X): T & U & V & W & X;
    /**
     * Merge the contents of two or more objects together into the first object.
     * @param target An object that will receive the new properties if additional objects are passed in or that will
     *               extend the jQuery namespace if it is the sole argument.
     * @param object1 An object containing additional properties to merge in.
     * @param object2 An object containing additional properties to merge in.
     * @param object3 An object containing additional properties to merge in.
     * @see \`{@link https://api.jquery.com/jQuery.extend/ }\`
     * @since 1.0
     * @example ​ ````Merge two objects, modifying the first.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.extend demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<div id="log"></div>
​
<script>
var object1 = {
  apple: 0,
  banana: { weight: 52, price: 100 },
  cherry: 97
};
var object2 = {
  banana: { price: 200 },
  durian: 100
};
​
// Merge object2 into object1
$.extend( object1, object2 );
​
// Assuming JSON.stringify - not available in IE<8
$( "#log" ).append( JSON.stringify( object1 ) );
</script>
​
</body>
</html>
```
     * @example ​ ````Merge defaults and options, without modifying the defaults. This is a common plugin development pattern.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.extend demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<div id="log"></div>
​
<script>
var defaults = { validate: false, limit: 5, name: "foo" };
var options = { validate: true, name: "bar" };
​
// Merge defaults and options, without modifying defaults
var settings = $.extend( {}, defaults, options );
​
// Assuming JSON.stringify - not available in IE<8
$( "#log" ).append( "<div><b>defaults -- </b>" + JSON.stringify( defaults ) + "</div>" );
$( "#log" ).append( "<div><b>options -- </b>" + JSON.stringify( options ) + "</div>" );
$( "#log" ).append( "<div><b>settings -- </b>" + JSON.stringify( settings ) + "</div>" );
</script>
​
</body>
</html>
```
     */
    extend<T, U, V, W>(target: T, object1: U, object2: V, object3: W): T & U & V & W;
    /**
     * Merge the contents of two or more objects together into the first object.
     * @param target An object that will receive the new properties if additional objects are passed in or that will
     *               extend the jQuery namespace if it is the sole argument.
     * @param object1 An object containing additional properties to merge in.
     * @param object2 An object containing additional properties to merge in.
     * @see \`{@link https://api.jquery.com/jQuery.extend/ }\`
     * @since 1.0
     * @example ​ ````Merge two objects, modifying the first.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.extend demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<div id="log"></div>
​
<script>
var object1 = {
  apple: 0,
  banana: { weight: 52, price: 100 },
  cherry: 97
};
var object2 = {
  banana: { price: 200 },
  durian: 100
};
​
// Merge object2 into object1
$.extend( object1, object2 );
​
// Assuming JSON.stringify - not available in IE<8
$( "#log" ).append( JSON.stringify( object1 ) );
</script>
​
</body>
</html>
```
     * @example ​ ````Merge defaults and options, without modifying the defaults. This is a common plugin development pattern.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.extend demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<div id="log"></div>
​
<script>
var defaults = { validate: false, limit: 5, name: "foo" };
var options = { validate: true, name: "bar" };
​
// Merge defaults and options, without modifying defaults
var settings = $.extend( {}, defaults, options );
​
// Assuming JSON.stringify - not available in IE<8
$( "#log" ).append( "<div><b>defaults -- </b>" + JSON.stringify( defaults ) + "</div>" );
$( "#log" ).append( "<div><b>options -- </b>" + JSON.stringify( options ) + "</div>" );
$( "#log" ).append( "<div><b>settings -- </b>" + JSON.stringify( settings ) + "</div>" );
</script>
​
</body>
</html>
```
     */
    extend<T, U, V>(target: T, object1: U, object2: V): T & U & V;
    /**
     * Merge the contents of two or more objects together into the first object.
     * @param target An object that will receive the new properties if additional objects are passed in or that will
     *               extend the jQuery namespace if it is the sole argument.
     * @param object1 An object containing additional properties to merge in.
     * @see \`{@link https://api.jquery.com/jQuery.extend/ }\`
     * @since 1.0
     * @example ​ ````Merge two objects, modifying the first.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.extend demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<div id="log"></div>
​
<script>
var object1 = {
  apple: 0,
  banana: { weight: 52, price: 100 },
  cherry: 97
};
var object2 = {
  banana: { price: 200 },
  durian: 100
};
​
// Merge object2 into object1
$.extend( object1, object2 );
​
// Assuming JSON.stringify - not available in IE<8
$( "#log" ).append( JSON.stringify( object1 ) );
</script>
​
</body>
</html>
```
     * @example ​ ````Merge defaults and options, without modifying the defaults. This is a common plugin development pattern.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.extend demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<div id="log"></div>
​
<script>
var defaults = { validate: false, limit: 5, name: "foo" };
var options = { validate: true, name: "bar" };
​
// Merge defaults and options, without modifying defaults
var settings = $.extend( {}, defaults, options );
​
// Assuming JSON.stringify - not available in IE<8
$( "#log" ).append( "<div><b>defaults -- </b>" + JSON.stringify( defaults ) + "</div>" );
$( "#log" ).append( "<div><b>options -- </b>" + JSON.stringify( options ) + "</div>" );
$( "#log" ).append( "<div><b>settings -- </b>" + JSON.stringify( settings ) + "</div>" );
</script>
​
</body>
</html>
```
     */
    extend<T, U>(target: T, object1: U): T & U;
    /**
     * Merge the contents of two or more objects together into the first object.
     * @param target An object that will receive the new properties if additional objects are passed in or that will
     *               extend the jQuery namespace if it is the sole argument.
     * @see \`{@link https://api.jquery.com/jQuery.extend/ }\`
     * @since 1.0
     */
    extend<T>(target: T): this & T;
    /**
     * Merge the contents of two or more objects together into the first object.
     * @param target An object that will receive the new properties if additional objects are passed in or that will
     *               extend the jQuery namespace if it is the sole argument.
     * @param object1 An object containing additional properties to merge in.
     * @param objectN Additional objects containing properties to merge in.
     * @see \`{@link https://api.jquery.com/jQuery.extend/ }\`
     * @since 1.0
     * @example ​ ````Merge two objects, modifying the first.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.extend demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<div id="log"></div>
​
<script>
var object1 = {
  apple: 0,
  banana: { weight: 52, price: 100 },
  cherry: 97
};
var object2 = {
  banana: { price: 200 },
  durian: 100
};
​
// Merge object2 into object1
$.extend( object1, object2 );
​
// Assuming JSON.stringify - not available in IE<8
$( "#log" ).append( JSON.stringify( object1 ) );
</script>
​
</body>
</html>
```
     * @example ​ ````Merge defaults and options, without modifying the defaults. This is a common plugin development pattern.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.extend demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<div id="log"></div>
​
<script>
var defaults = { validate: false, limit: 5, name: "foo" };
var options = { validate: true, name: "bar" };
​
// Merge defaults and options, without modifying defaults
var settings = $.extend( {}, defaults, options );
​
// Assuming JSON.stringify - not available in IE<8
$( "#log" ).append( "<div><b>defaults -- </b>" + JSON.stringify( defaults ) + "</div>" );
$( "#log" ).append( "<div><b>options -- </b>" + JSON.stringify( options ) + "</div>" );
$( "#log" ).append( "<div><b>settings -- </b>" + JSON.stringify( settings ) + "</div>" );
</script>
​
</body>
</html>
```
     */
    extend(target: any, object1: any, ...objectN: any[]): any;
    /**
     * Load data from the server using a HTTP GET request.
     * @param url A string containing the URL to which the request is sent.
     * @param data A plain object or string that is sent to the server with the request.
     * @param success A callback function that is executed if the request succeeds. Required if `dataType` is provided,
     *                but you can use `null` or \`{@link noop jQuery.noop}\` as a placeholder.
     * @param dataType The type of data expected from the server. Default: Intelligent Guess (xml, json, script, text, html).
     * @see \`{@link https://api.jquery.com/jQuery.get/ }\`
     * @since 1.0
     */
    get(url: string,
        data: JQuery.PlainObject | string,
        success: JQuery.jqXHR.DoneCallback | null,
        dataType?: string): JQuery.jqXHR;
    /**
     * Load data from the server using a HTTP GET request.
     * @param url A string containing the URL to which the request is sent.
     * @param success A callback function that is executed if the request succeeds. Required if `dataType` is provided,
     *                but you can use `null` or \`{@link noop jQuery.noop}\` as a placeholder.
     * @param dataType The type of data expected from the server. Default: Intelligent Guess (xml, json, script, text, html).
     * @see \`{@link https://api.jquery.com/jQuery.get/ }\`
     * @since 1.0
     * @example ​ ````Get the test.php page contents, which has been returned in json format (&lt;?php echo json_encode( array( &quot;name&quot;=&gt;&quot;John&quot;,&quot;time&quot;=&gt;&quot;2pm&quot; ) ); ?&gt;), and add it to the page.
```javascript
$.get( "test.php", function( data ) {
  $( "body" )
    .append( "Name: " + data.name ) // John
    .append( "Time: " + data.time ); //  2pm
}, "json" );
```
     */
    get(url: string,
        success: JQuery.jqXHR.DoneCallback | null,
        dataType: string): JQuery.jqXHR;
    /**
     * Load data from the server using a HTTP GET request.
     * @param url A string containing the URL to which the request is sent.
     * @param success_data _&#x40;param_ `success_data`
     * <br>
     * * `success` — A callback function that is executed if the request succeeds. Required if `dataType` is provided,
     *               but you can use `null` or \`{@link noop jQuery.noop}\` as a placeholder. <br>
     * * `data` — A plain object or string that is sent to the server with the request.
     * @see \`{@link https://api.jquery.com/jQuery.get/ }\`
     * @since 1.0
     * @example ​ ````Request the test.php page and send some additional data along (while still ignoring the return results).
```javascript
$.get( "test.php", { name: "John", time: "2pm" } );
```
     * @example ​ ````Pass arrays of data to the server (while still ignoring the return results).
```javascript
$.get( "test.php", { "choices[]": ["Jon", "Susan"] } );
```
     * @example ​ ````Alert the results from requesting test.php (HTML or XML, depending on what was returned).
```javascript
$.get( "test.php", function( data ) {
  alert( "Data Loaded: " + data );
});
```
     * @example ​ ````Alert the results from requesting test.cgi with an additional payload of data (HTML or XML, depending on what was returned).
```javascript
$.get( "test.cgi", { name: "John", time: "2pm" } )
  .done(function( data ) {
    alert( "Data Loaded: " + data );
  });
```
     */
    get(url: string,
        success_data: JQuery.jqXHR.DoneCallback | JQuery.PlainObject | string): JQuery.jqXHR;
    /**
     * Load data from the server using a HTTP GET request.
     * @param url_settings _&#x40;param_ `url_settings`
     * <br>
     * * `url` — A string containing the URL to which the request is sent. <br>
     * * `settings` — A set of key/value pairs that configure the Ajax request. All properties except for `url` are
     *                optional. A default can be set for any option with \`{@link ajaxSetup $.ajaxSetup()}\`. See \`{@link https://api.jquery.com/jquery.ajax/#jQuery-ajax-settings jQuery.ajax( settings )}\`
     *                for a complete list of all settings. The type option will automatically be set to `GET`.
     * @see \`{@link https://api.jquery.com/jQuery.get/ }\`
     * @since 1.0
     * @since 1.12
     * @since 2.2
     * @example ​ ````Request the test.php page, but ignore the return results.
```javascript
$.get( "test.php" );
```
     */
    get(url_settings?: string | JQuery.UrlAjaxSettings): JQuery.jqXHR;
    /**
     * Load JSON-encoded data from the server using a GET HTTP request.
     * @param url A string containing the URL to which the request is sent.
     * @param data A plain object or string that is sent to the server with the request.
     * @param success A callback function that is executed if the request succeeds.
     * @see \`{@link https://api.jquery.com/jQuery.getJSON/ }\`
     * @since 1.0
     */
    getJSON(url: string,
            data: JQuery.PlainObject | string,
            success: JQuery.jqXHR.DoneCallback): JQuery.jqXHR;
    /**
     * Load JSON-encoded data from the server using a GET HTTP request.
     * @param url A string containing the URL to which the request is sent.
     * @param success_data _&#x40;param_ `url_settings`
     * <br>
     * * `success` — A callback function that is executed if the request succeeds. <br>
     * * `data` — A plain object or string that is sent to the server with the request.
     * @see \`{@link https://api.jquery.com/jQuery.getJSON/ }\`
     * @since 1.0
     * @example ​ ````Loads the four most recent pictures of Mount Rainier from the Flickr JSONP API.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.getJSON demo</title>
  <style>
  img {
    height: 100px;
    float: left;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<div id="images"></div>
​
<script>
(function() {
  var flickerAPI = "https://api.flickr.com/services/feeds/photos_public.gne?jsoncallback=?";
  $.getJSON( flickerAPI, {
    tags: "mount rainier",
    tagmode: "any",
    format: "json"
  })
    .done(function( data ) {
      $.each( data.items, function( i, item ) {
        $( "<img>" ).attr( "src", item.media.m ).appendTo( "#images" );
        if ( i === 3 ) {
          return false;
        }
      });
    });
})();
</script>
​
</body>
</html>
```
     * @example ​ ````Load the JSON data from test.js and access a name from the returned JSON data.
```javascript
$.getJSON( "test.js", function( json ) {
  console.log( "JSON Data: " + json.users[ 3 ].name );
 });
 ```
     * @example ​ ````Load the JSON data from test.js, passing along additional data, and access a name from the returned JSON data.
      If an error occurs, log an error message instead.
```javascript
$.getJSON( "test.js", { name: "John", time: "2pm" } )
  .done(function( json ) {
    console.log( "JSON Data: " + json.users[ 3 ].name );
  })
  .fail(function( jqxhr, textStatus, error ) {
    var err = textStatus + ", " + error;
    console.log( "Request Failed: " + err );
});
```
     */
    getJSON(url: string,
            success_data?: JQuery.jqXHR.DoneCallback | JQuery.PlainObject | string): JQuery.jqXHR;
    /**
     * Load a JavaScript file from the server using a GET HTTP request, then execute it.
     * @param url A string containing the URL to which the request is sent.
     * @param success A callback function that is executed if the request succeeds.
     * @see \`{@link https://api.jquery.com/jQuery.getScript/ }\`
     * @since 1.0
     * @example ​ ````Define a $.cachedScript() method that allows fetching a cached script:
```javascript
jQuery.cachedScript = function( url, options ) {
​
  // Allow user to set any option except for dataType, cache, and url
  options = $.extend( options || {}, {
    dataType: "script",
    cache: true,
    url: url
  });
​
  // Use $.ajax() since it is more flexible than $.getScript
  // Return the jqXHR object so we can chain callbacks
  return jQuery.ajax( options );
};
​
// Usage
$.cachedScript( "ajax/test.js" ).done(function( script, textStatus ) {
  console.log( textStatus );
});
```
     * @example ​ ````Load the official jQuery Color Animation plugin dynamically and bind some color animations to occur once the new functionality is loaded.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.getScript demo</title>
  <style>
  .block {
     background-color: blue;
     width: 150px;
     height: 70px;
     margin: 10px;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<button id="go">&raquo; Run</button>
<div class="block"></div>
​
<script>
var url = "https://code.jquery.com/color/jquery.color.js";
$.getScript( url, function() {
  $( "#go" ).click(function() {
    $( ".block" )
      .animate({
        backgroundColor: "rgb(255, 180, 180)"
      }, 1000 )
      .delay( 500 )
      .animate({
        backgroundColor: "olive"
      }, 1000 )
      .delay( 500 )
      .animate({
        backgroundColor: "#00f"
      }, 1000 );
  });
});
</script>
​
</body>
</html>
```
     */
    getScript(url: string,
              success?: JQuery.jqXHR.DoneCallback<string | undefined>): JQuery.jqXHR<string | undefined>;
    /**
     * Load a JavaScript file from the server using a GET HTTP request, then execute it.
     * @see \`{@link https://api.jquery.com/jQuery.getScript/ }\`
     * @since 1.12
     * @since 2.2
     */
    getScript(options: JQuery.UrlAjaxSettings): JQuery.jqXHR<string | undefined>;
    /**
     * Execute some JavaScript code globally.
     * @param code The JavaScript code to execute.
     * @see \`{@link https://api.jquery.com/jQuery.globalEval/ }\`
     * @since 1.0.4
     * @example ​ ````Execute a script in the global context.
```javascript
function test() {
  jQuery.globalEval( "var newVar = true;" )
}
test();
// newVar === true
```
     */
    globalEval(code: string): void;
    /**
     * Finds the elements of an array which satisfy a filter function. The original array is not affected.
     * @param array The array-like object to search through.
     * @param funсtion The function to process each item against. The first argument to the function is the item, and the
     *                 second argument is the index. The function should return a Boolean value. `this` will be the global
     *                 window object.
     * @param invert If "invert" is false, or not provided, then the function returns an array consisting of all elements
     *               for which "callback" returns true. If "invert" is true, then the function returns an array
     *               consisting of all elements for which "callback" returns false.
     * @see \`{@link https://api.jquery.com/jQuery.grep/ }\`
     * @since 1.0
     * @example ​ ````Filters the original array of numbers leaving that are not 5 and have an index greater than 4.  Then it removes all 9s.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.grep demo</title>
  <style>
  div {
    color: blue;
  }
  p {
    color: green;
    margin: 0;
  }
  span {
    color: red;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<div></div>
<p></p>
<span></span>
​
<script>
var arr = [ 1, 9, 3, 8, 6, 1, 5, 9, 4, 7, 3, 8, 6, 9, 1 ];
$( "div" ).text( arr.join( ", " ) );
​
arr = jQuery.grep(arr, function( n, i ) {
  return ( n !== 5 && i > 4 );
});
$( "p" ).text( arr.join( ", " ) );
​
arr = jQuery.grep(arr, function( a ) {
  return a !== 9;
});
​
$( "span" ).text( arr.join( ", " ) );
</script>
​
</body>
</html>
```
     * @example ​ ````Filter an array of numbers to include only numbers bigger then zero.
```javascript
$.grep( [ 0, 1, 2 ], function( n, i ) {
  return n > 0;
});
```
     * @example ​ ````Filter an array of numbers to include numbers that are not bigger than zero.
```javascript
$.grep( [ 0, 1, 2 ], function( n, i ) {
    return n > 0;
}, true );
```
     */
    grep<T>(array: ArrayLike<T>,
            funсtion: (elementOfArray: T, indexInArray: number) => boolean,
            invert?: boolean): T[];
    /**
     * Determine whether an element has any jQuery data associated with it.
     * @param element A DOM element to be checked for data.
     * @see \`{@link https://api.jquery.com/jQuery.hasData/ }\`
     * @since 1.5
     * @example ​ ````Set data on an element and see the results of hasData.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.hasData demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p>Results: </p>
​
<script>
var $p = jQuery( "p" ), p = $p[ 0 ];
$p.append( jQuery.hasData( p ) + " " ); // false
​
$.data( p, "testing", 123 );
$p.append( jQuery.hasData( p ) + " " ); // true
​
$.removeData( p, "testing" );
$p.append( jQuery.hasData( p ) + " " ); // false
​
$p.on( "click", function() {} );
$p.append( jQuery.hasData( p ) + " " ); // true
​
$p.off( "click" );
$p.append( jQuery.hasData( p ) + " " ); // false
</script>
​
</body>
</html>
```
     */
    hasData(element: Element | Document | Window | JQuery.PlainObject): boolean;
    /**
     * Holds or releases the execution of jQuery's ready event.
     * @param hold Indicates whether the ready hold is being requested or released
     * @see \`{@link https://api.jquery.com/jQuery.holdReady/ }\`
     * @since 1.6
     * @deprecated ​ Deprecated since 3.2. See \`{@link https://github.com/jquery/jquery/issues/3288 }\`.
     *
     * **Cause**: The `jQuery.holdReady()` method has been deprecated due to its detrimental effect on the global performance of the page. This method can prevent all the code on the page from initializing for extended lengths of time.
     *
     * **Solution**: Rewrite the page so that it does not require all jQuery ready handlers to be delayed. This might be accomplished, for example, by late-loading only the code that requires the delay when it is safe to run. Due to the complexity of this method, jQuery Migrate does not attempt to fill the functionality. If the underlying version of jQuery used with jQuery Migrate no longer contains `jQuery.holdReady()` the code will fail shortly after this warning appears.
     * @example ​ ````Delay the ready event until a custom plugin has loaded.
```javascript
$.holdReady( true );
$.getScript( "myplugin.js", function() {
  $.holdReady( false );
});
```
     */
    holdReady(hold: boolean): void;
    /**
     * Modify and filter HTML strings passed through jQuery manipulation methods.
     * @param html The HTML string on which to operate.
     * @see \`{@link https://api.jquery.com/jQuery.htmlPrefilter/ }\`
     * @since 1.12
     * @since 2.2
     */
    htmlPrefilter(html: JQuery.htmlString): JQuery.htmlString;
    /**
     * Search for a specified value within an array and return its index (or -1 if not found).
     * @param value The value to search for.
     * @param array An array through which to search.
     * @param fromIndex The index of the array at which to begin the search. The default is 0, which will search the whole array.
     * @see \`{@link https://api.jquery.com/jQuery.inArray/ }\`
     * @since 1.2
     * @example ​ ````Report the index of some elements in the array.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.inArray demo</title>
  <style>
  div {
    color: blue;
  }
  span {
    color: red;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<div>"John" found at <span></span></div>
<div>4 found at <span></span></div>
<div>"Karl" not found, so <span></span></div>
<div>"Pete" is in the array, but not at or after index 2, so <span></span></div>
​
<script>
var arr = [ 4, "Pete", 8, "John" ];
var $spans = $( "span" );
$spans.eq( 0 ).text( jQuery.inArray( "John", arr ) );
$spans.eq( 1 ).text( jQuery.inArray( 4, arr ) );
$spans.eq( 2 ).text( jQuery.inArray( "Karl", arr ) );
$spans.eq( 3 ).text( jQuery.inArray( "Pete", arr, 2 ) );
</script>
​
</body>
</html>
```
     */
    inArray<T>(value: T, array: T[], fromIndex?: number): number;
    /**
     * Determine whether the argument is an array.
     * @param obj Object to test whether or not it is an array.
     * @see \`{@link https://api.jquery.com/jQuery.isArray/ }\`
     * @since 1.3
     * @deprecated ​ Deprecated since 3.2. Use \`{@link ArrayConstructor.isArray Array.isArray}\`.
     * @example ​ ````Finds out if the parameter is an array.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.isArray demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
Is [] an Array? <b></b>
​
<script>
$( "b" ).append( "" + $.isArray([]) );
</script>
​
</body>
</html>
```
     */
    isArray(obj: any): obj is any[];
    /**
     * Check to see if an object is empty (contains no enumerable properties).
     * @param obj The object that will be checked to see if it's empty.
     * @see \`{@link https://api.jquery.com/jQuery.isEmptyObject/ }\`
     * @since 1.4
     * @example ​ ````Check an object to see if it&#39;s empty.
```javascript
jQuery.isEmptyObject({}); // true
jQuery.isEmptyObject({ foo: "bar" }); // false
```
     */
    isEmptyObject(obj: any): boolean;
    /**
     * Determine if the argument passed is a JavaScript function object.
     * @param obj Object to test whether or not it is a function.
     * @see \`{@link https://api.jquery.com/jQuery.isFunction/ }\`
     * @since 1.2
     * @deprecated ​ Deprecated since 3.3. Use `typeof x === "function"`.
     * @example ​ ````Test a few parameter examples.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.isFunction demo</title>
  <style>
  div {
    color: blue;
    margin: 2px;
    font-size: 14px;
  }
  span {
    color: red;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<div>jQuery.isFunction( objs[ 0 ] ) = <span></span></div>
<div>jQuery.isFunction( objs[ 1 ] ) = <span></span></div>
<div>jQuery.isFunction( objs[ 2 ] ) = <span></span></div>
<div>jQuery.isFunction( objs[ 3 ] ) = <span></span></div>
<div>jQuery.isFunction( objs[ 4 ] ) = <span></span></div>
​
<script>
function stub() {}
var objs = [
  function() {},
  { x:15, y:20 },
  null,
  stub,
  "function"
];
​
jQuery.each( objs, function( i ) {
  var isFunc = jQuery.isFunction( objs[ i ]);
  $( "span" ).eq( i ).text( isFunc );
});
</script>
​
</body>
</html>
```
     * @example ​ ````Finds out if the parameter is a function.
```javascript
$.isFunction(function() {});
```
     */
    // tslint:disable-next-line:ban-types
    isFunction(obj: any): obj is Function;
    /**
     * Determines whether its argument represents a JavaScript number.
     * @param value The value to be tested.
     * @see \`{@link https://api.jquery.com/jQuery.isNumeric/ }\`
     * @since 1.7
     * @deprecated ​ Deprecated since 3.3. Internal. See \`{@link https://github.com/jquery/jquery/issues/2960 }\`.
     * @example ​ ````Sample return values of $.isNumeric with various inputs.
```javascript
// true (numeric)
$.isNumeric( "-10" )
$.isNumeric( "0" )
$.isNumeric( 0xFF )
$.isNumeric( "0xFF" )
$.isNumeric( "8e5" )
$.isNumeric( "3.1415" )
$.isNumeric( +10 )
$.isNumeric( 0144 )
​
// false (non-numeric)
$.isNumeric( "-0x42" )
$.isNumeric( "7.2acdgs" )
$.isNumeric( "" )
$.isNumeric( {} )
$.isNumeric( NaN )
$.isNumeric( null )
$.isNumeric( true )
$.isNumeric( Infinity )
$.isNumeric( undefined )
```
     */
    isNumeric(value: any): boolean;
    /**
     * Check to see if an object is a plain object (created using "{}" or "new Object").
     * @param obj The object that will be checked to see if it's a plain object.
     * @see \`{@link https://api.jquery.com/jQuery.isPlainObject/ }\`
     * @since 1.4
     * @example ​ ````Check an object to see if it&#39;s a plain object.
```javascript
jQuery.isPlainObject({}) // true
jQuery.isPlainObject( "test" ) // false
```
     */
    isPlainObject(obj: any): boolean;
    /**
     * Determine whether the argument is a window.
     * @param obj Object to test whether or not it is a window.
     * @see \`{@link https://api.jquery.com/jQuery.isWindow/ }\`
     * @since 1.4.3
     * @deprecated ​ Deprecated since 3.3. Internal. See \`{@link https://github.com/jquery/jquery/issues/3629 }\`.
     *
     * **Cause**: This method returns `true` if its argument is thought to be a `window` element. It was created for internal use and is not a reliable way of detecting `window` for public needs.
     *
     * **Solution**: Remove any use of `jQuery.isWindow()` from code. If it is truly needed it can be replaced with a check for `obj != null && obj === obj.window` which was the test used inside this method.
     * @example ​ ````Finds out if the parameter is a window.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.isWindow demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
Is 'window' a window? <b></b>
​
<script>
$( "b" ).append( "" + $.isWindow( window ) );
</script>
​
</body>
</html>
```
     */
    isWindow(obj: any): obj is Window;
    /**
     * Check to see if a DOM node is within an XML document (or is an XML document).
     * @param node The DOM node that will be checked to see if it's in an XML document.
     * @see \`{@link https://api.jquery.com/jQuery.isXMLDoc/ }\`
     * @since 1.1.4
     * @example ​ ````Check an object to see if it&#39;s in an XML document.
```javascript
jQuery.isXMLDoc( document ) // false
jQuery.isXMLDoc( document.body ) // false
```
     */
    isXMLDoc(node: Node): boolean;
    /**
     * Convert an array-like object into a true JavaScript array.
     * @param obj Any object to turn into a native Array.
     * @see \`{@link https://api.jquery.com/jQuery.makeArray/ }\`
     * @since 1.2
     * @example ​ ````Turn a collection of HTMLElements into an Array of them.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.makeArray demo</title>
  <style>
  div {
    color: red;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<div>First</div>
<div>Second</div>
<div>Third</div>
<div>Fourth</div>
​
<script>
// Returns a NodeList
var elems = document.getElementsByTagName( "div" );
// Convert the NodeList to an Array
var arr = jQuery.makeArray( elems );
// Use an Array method on list of dom elements
arr.reverse();
$( arr ).appendTo( document.body );
</script>
​
</body>
</html>
```
     * @example ​ ````Turn a jQuery object into an array
```javascript
var obj = $( "li" );
var arr = $.makeArray( obj );
```
     */
    makeArray<T>(obj: ArrayLike<T>): T[];
    /**
     * Translate all items in an array or object to new array of items.
     * @param array The Array to translate.
     * @param callback The function to process each item against. The first argument to the function is the array item, the
     *                 second argument is the index in array The function can return any value. A returned array will be
     *                 flattened into the resulting array. Within the function, this refers to the global (window) object.
     * @see \`{@link https://api.jquery.com/jQuery.map/ }\`
     * @since 1.0
     * @example ​ ````Use $.map() to change the values of an array.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.map demo</title>
  <style>
  div {
    color: blue;
  }
  p {
    color: green;
    margin: 0;
  }
  span {
    color: red;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<div></div>
<p></p>
<span></span>
​
<script>
var arr = [ "a", "b", "c", "d", "e" ];
$( "div" ).text( arr.join( ", " ) );
​
arr = jQuery.map( arr, function( n, i ) {
  return ( n.toUpperCase() + i );
});
$( "p" ).text( arr.join( ", " ) );
​
arr = jQuery.map( arr, function( a ) {
  return a + a;
});
$( "span" ).text( arr.join( ", " ) );
</script>
​
</body>
</html>
```
     * @example ​ ````Map the original array to a new one and add 4 to each value.
```javascript
$.map( [ 0, 1, 2 ], function( n ) {
  return n + 4;
});
```
     * @example ​ ````Map the original array to a new one, adding 1 to each value if it is bigger then zero and removing it if not.
```javascript
$.map( [ 0, 1, 2 ], function( n ) {
  return n > 0 ? n + 1 : null;
});
```
     * @example ​ ````Map the original array to a new one; each element is added with its original value and the value plus one.
```javascript
$.map( [ 0, 1, 2 ], function( n ) {
    return [ n, n + 1 ];
});
```
     * @example ​ ````Map the original array to a new one; each element is squared.
```javascript
$.map( [ 0, 1, 2, 3 ], function( a ) {
  return a * a;
});
```
     * @example ​ ````Map the original array to a new one, removing numbers less than 50 by returning null and subtracting 45 from the rest.
```javascript
$.map( [ 0, 1, 52, 97 ], function( a ) {
  return (a > 50 ? a - 45 : null);
});
```
     * @example ​ ````Augment the resulting array by returning an array inside the function.
```javascript
var array = [ 0, 1, 52, 97 ];
array = $.map( array, function( a, index ) {
  return [ a - 45, index ];
});
```
     */
    map<T, TReturn>(array: T[], callback: (this: Window, elementOfArray: T, indexInArray: number) => JQuery.TypeOrArray<TReturn> | null | undefined): TReturn[];
    /**
     * Translate all items in an array or object to new array of items.
     * @param obj The Object to translate.
     * @param callback The function to process each item against. The first argument to the function is the value; the
     *                 second argument is the key of the object property. The function can return any value to add to the
     *                 array. A returned array will be flattened into the resulting array. Within the function, this refers
     *                 to the global (window) object.
     * @see \`{@link https://api.jquery.com/jQuery.map/ }\`
     * @since 1.6
     * @example ​ ````Map the original object to a new array and double each value.
```javascript
var dimensions = { width: 10, height: 15, length: 20 };
dimensions = $.map( dimensions, function( value, index ) {
  return value * 2;
});
```
     * @example ​ ````Map an object&#39;s keys to an array.
```javascript
var dimensions = { width: 10, height: 15, length: 20 };
var keys = $.map( dimensions, function( value, key ) {
  return key;
});
```
     */
    map<T, K extends keyof T, TReturn>(obj: T, callback: (this: Window, propertyOfObject: T[K], key: K) => JQuery.TypeOrArray<TReturn> | null | undefined): TReturn[];
    /**
     * Merge the contents of two arrays together into the first array.
     * @param first The first array-like object to merge, the elements of second added.
     * @param second The second array-like object to merge into the first, unaltered.
     * @see \`{@link https://api.jquery.com/jQuery.merge/ }\`
     * @since 1.0
     * @example ​ ````Merges two arrays, altering the first argument.
```javascript
$.merge( [ 0, 1, 2 ], [ 2, 3, 4 ] )
```
     * @example ​ ````Merges two arrays, altering the first argument.
```javascript
$.merge( [ 3, 2, 1 ], [ 4, 3, 2 ] )
```
     * @example ​ ````Merges two arrays, but uses a copy, so the original isn&#39;t altered.
```javascript
var first = [ "a", "b", "c" ];
var second = [ "d", "e", "f" ];
$.merge( $.merge( [], first ), second );
```
     */
    merge<T, U>(first: ArrayLike<T>, second: ArrayLike<U>): Array<T | U>;
    /**
     * Relinquish jQuery's control of the $ variable.
     * @param removeAll A Boolean indicating whether to remove all jQuery variables from the global scope (including jQuery itself).
     * @see \`{@link https://api.jquery.com/jQuery.noConflict/ }\`
     * @since 1.0
     * @example ​ ````Map the original object that was referenced by $ back to $.
```javascript
jQuery.noConflict();
// Do something with jQuery
jQuery( "div p" ).hide();
// Do something with another library's $()
$( "content" ).style.display = "none";
```
     * @example ​ ````Revert the $ alias and then create and execute a function to provide the $ as a jQuery alias inside the function&#39;s scope. Inside the function the original $ object is not available. This works well for most plugins that don&#39;t rely on any other library.
```javascript
jQuery.noConflict();
(function( $ ) {
  $(function() {
    // More code using $ as alias to jQuery
  });
})(jQuery);
​
// Other code using $ as an alias to the other library
```
     * @example ​ ````Create a different alias instead of jQuery to use in the rest of the script.
```javascript
var j = jQuery.noConflict();
​
// Do something with jQuery
j( "div p" ).hide();
​
// Do something with another library's $()
$( "content" ).style.display = "none";
```
     * @example ​ ````Completely move jQuery to a new namespace in another object.
```javascript
var dom = {};
dom.query = jQuery.noConflict( true );
```
     * @example ​ ````Load two versions of jQuery (not recommended). Then, restore jQuery&#39;s globally scoped variables to the first loaded jQuery.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.noConflict demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<div id="log">
  <h3>Before $.noConflict(true)</h3>
</div>
<script src="https://code.jquery.com/jquery-1.6.2.js"></script>
​
<script>
var $log = $( "#log" );
​
$log.append( "2nd loaded jQuery version ($): " + $.fn.jquery + "<br>" );
​
// Restore globally scoped jQuery variables to the first version loaded
// (the newer version)
​
jq162 = jQuery.noConflict( true );
​
$log.append( "<h3>After $.noConflict(true)</h3>" );
$log.append( "1st loaded jQuery version ($): " + $.fn.jquery + "<br>" );
$log.append( "2nd loaded jQuery version (jq162): " + jq162.fn.jquery + "<br>" );
</script>
​
</body>
</html>
```
     */
    noConflict(removeAll?: boolean): this;
    /**
     * @deprecated ​ Deprecated since 3.2.
     *
     * **Cause**: This public but never-documented method has been deprecated as of jQuery 3.2.0.
     *
     * **Solution**: Replace calls such as `jQuery.nodeName( elem, "div" )` with a test such as `elem.nodeName.toLowerCase() === "div"`.
     */
    nodeName(elem: Node, name: string): boolean;
    /**
     * An empty function.
     * @see \`{@link https://api.jquery.com/jQuery.noop/ }\`
     * @since 1.4
     */
    noop(): undefined;
    /**
     * Return a number representing the current time.
     * @see \`{@link https://api.jquery.com/jQuery.now/ }\`
     * @since 1.4.3
     * @deprecated ​ Deprecated since 3.3. Use \`{@link DateConstructor.now Date.now}\`.
     */
    now(): number;
    /**
     * Create a serialized representation of an array, a plain object, or a jQuery object suitable for use in a URL query string or Ajax request. In case a jQuery object is passed, it should contain input elements with name/value properties.
     * @param obj An array, a plain object, or a jQuery object to serialize.
     * @param traditional A Boolean indicating whether to perform a traditional "shallow" serialization.
     * @see \`{@link https://api.jquery.com/jQuery.param/ }\`
     * @since 1.2
     * @since 1.4
     * @example ​ ````Serialize a key/value object.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.param demo</title>
  <style>
  div {
    color: red;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<div id="results"></div>
​
<script>
var params = { width:1680, height:1050 };
var str = jQuery.param( params );
$( "#results" ).text( str );
</script>
​
</body>
</html>
```
     * @example ​ ````Serialize a few complex objects
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.param demo</title>
  <style>
  div {
    color: red;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​​
<script>
// <=1.3.2:
$.param({ a: [ 2, 3, 4 ] }); // "a=2&a=3&a=4"
// >=1.4:
$.param({ a: [ 2, 3, 4 ] }); // "a[]=2&a[]=3&a[]=4"
​
// <=1.3.2:
$.param({ a: { b: 1, c: 2 }, d: [ 3, 4, { e: 5 } ] });
// "a=[object+Object]&d=3&d=4&d=[object+Object]"
​
// >=1.4:
$.param({ a: { b: 1, c: 2 }, d: [ 3, 4, { e: 5 } ] });
// "a[b]=1&a[c]=2&d[]=3&d[]=4&d[2][e]=5"
</script>
​
</body>
</html>
```
     */
    param(obj: any[] | JQuery.PlainObject | JQuery, traditional?: boolean): string;
    /**
     * Parses a string into an array of DOM nodes.
     * @param data HTML string to be parsed
     * @param context Document element to serve as the context in which the HTML fragment will be created
     * @param keepScripts A Boolean indicating whether to include scripts passed in the HTML string
     * @see \`{@link https://api.jquery.com/jQuery.parseHTML/ }\`
     * @since 1.8
     */
    parseHTML(data: string, context: Document | null | undefined, keepScripts: boolean): JQuery.Node[];
    /**
     * Parses a string into an array of DOM nodes.
     * @param data HTML string to be parsed
     * @param context_keepScripts _&#x40;param_ `context_keepScripts`
     * <br>
     * * `context` — Document element to serve as the context in which the HTML fragment will be created <br>
     * * `keepScripts` — A Boolean indicating whether to include scripts passed in the HTML string
     * @see \`{@link https://api.jquery.com/jQuery.parseHTML/ }\`
     * @since 1.8
     * @example ​ ````Create an array of DOM nodes using an HTML string and insert it into a div.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.parseHTML demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<div id="log">
  <h3>Content:</h3>
</div>
​
<script>
var $log = $( "#log" ),
  str = "hello, <b>my name is</b> jQuery.",
  html = $.parseHTML( str ),
  nodeNames = [];
​
// Append the parsed HTML
$log.append( html );
​
// Gather the parsed HTML's node names
$.each( html, function( i, el ) {
  nodeNames[ i ] = "<li>" + el.nodeName + "</li>";
});
​
// Insert the node names
$log.append( "<h3>Node Names:</h3>" );
$( "<ol></ol>" )
  .append( nodeNames.join( "" ) )
  .appendTo( $log );
</script>
​
</body>
</html>
```
     */
    parseHTML(data: string, context_keepScripts?: Document | null | boolean): JQuery.Node[];
    /**
     * Takes a well-formed JSON string and returns the resulting JavaScript value.
     * @param json The JSON string to parse.
     * @see \`{@link https://api.jquery.com/jQuery.parseJSON/ }\`
     * @since 1.4.1
     * @deprecated ​ Deprecated since 3.0. Use \`{@link JSON.parse }\`.
     *
     * **Cause**: The `jQuery.parseJSON` method in recent jQuery is identical to the native `JSON.parse`. As of jQuery 3.0 `jQuery.parseJSON` is deprecated.
     *
     * **Solution**: Replace any use of `jQuery.parseJSON` with `JSON.parse`.
     * @example ​ ````Parse a JSON string.
```javascript
var obj = jQuery.parseJSON( '{ "name": "John" }' );
alert( obj.name === "John" );
```
     */
    parseJSON(json: string): any;
    /**
     * Parses a string into an XML document.
     * @param data a well-formed XML string to be parsed
     * @see \`{@link https://api.jquery.com/jQuery.parseXML/ }\`
     * @since 1.5
     * @example ​ ````Create a jQuery object using an XML string and obtain the value of the title node.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.parseXML demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p id="someElement"></p>
<p id="anotherElement"></p>
​
<script>
var xml = "<rss version='2.0'><channel><title>RSS Title</title></channel></rss>",
  xmlDoc = $.parseXML( xml ),
  $xml = $( xmlDoc ),
  $title = $xml.find( "title" );
​
// Append "RSS Title" to #someElement
$( "#someElement" ).append( $title.text() );
​
// Change the title to "XML Title"
$title.text( "XML Title" );
​
// Append "XML Title" to #anotherElement
$( "#anotherElement" ).append( $title.text() );
</script>
​
</body>
</html>
```
     */
    parseXML(data: string): XMLDocument;
    /**
     * Load data from the server using a HTTP POST request.
     * @param url A string containing the URL to which the request is sent.
     * @param data A plain object or string that is sent to the server with the request.
     * @param success A callback function that is executed if the request succeeds. Required if dataType is provided, but
     *                can be null in that case.
     * @param dataType The type of data expected from the server. Default: Intelligent Guess (xml, json, script, text, html).
     * @see \`{@link https://api.jquery.com/jQuery.post/ }\`
     * @since 1.0
     * @example ​ ````Post to the test.php page and get content which has been returned in json format (&lt;?php echo json_encode(array(&quot;name&quot;=&gt;&quot;John&quot;,&quot;time&quot;=&gt;&quot;2pm&quot;)); ?&gt;).
```javascript
$.post( "test.php", { func: "getNameAndTime" }, function( data ) {
  console.log( data.name ); // John
  console.log( data.time ); // 2pm
}, "json");
```
     */
    post(url: string,
         data: JQuery.PlainObject | string,
         success: JQuery.jqXHR.DoneCallback | null,
         dataType?: string): JQuery.jqXHR;
    /**
     * Load data from the server using a HTTP POST request.
     * @param url A string containing the URL to which the request is sent.
     * @param success A callback function that is executed if the request succeeds. Required if dataType is provided, but
     *                can be null in that case.
     * @param dataType The type of data expected from the server. Default: Intelligent Guess (xml, json, script, text, html).
     * @see \`{@link https://api.jquery.com/jQuery.post/ }\`
     * @since 1.0
     */
    post(url: string,
         success: JQuery.jqXHR.DoneCallback | null,
         dataType: string): JQuery.jqXHR;
    /**
     * Load data from the server using a HTTP POST request.
     * @param url A string containing the URL to which the request is sent.
     * @param success_data _&#x40;param_ `success_data`
     * <br>
     * * `success` — A callback function that is executed if the request succeeds. Required if `dataType` is provided,
     *               but can be `null` in that case. <br>
     * * `data` — A plain object or string that is sent to the server with the request.
     * @see \`{@link https://api.jquery.com/jQuery.post/ }\`
     * @since 1.0
     * @example ​ ````Request the test.php page and send some additional data along (while still ignoring the return results).
```javascript
$.post( "test.php", { name: "John", time: "2pm" } );
```
     * @example ​ ````Pass arrays of data to the server (while still ignoring the return results).
```javascript
$.post( "test.php", { 'choices[]': [ "Jon", "Susan" ] } );
```
     * @example ​ ````Send form data using Ajax requests
```javascript
$.post( "test.php", $( "#testform" ).serialize() );
```
     * @example ​ ````Alert the results from requesting test.php (HTML or XML, depending on what was returned).
```javascript
$.post( "test.php", function( data ) {
  alert( "Data Loaded: " + data );
});
```
     * @example ​ ````Alert the results from requesting test.php with an additional payload of data (HTML or XML, depending on what was returned).
```javascript
$.post( "test.php", { name: "John", time: "2pm" })
  .done(function( data ) {
    alert( "Data Loaded: " + data );
  });
```
     * @example ​ ````Post a form using Ajax and put results in a div
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.post demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<form action="/" id="searchForm">
  <input type="text" name="s" placeholder="Search...">
  <input type="submit" value="Search">
</form>
<!-- the result of the search will be rendered inside this div -->
<div id="result"></div>
​
<script>
// Attach a submit handler to the form
$( "#searchForm" ).submit(function( event ) {
​
  // Stop form from submitting normally
  event.preventDefault();
​
  // Get some values from elements on the page:
  var $form = $( this ),
    term = $form.find( "input[name='s']" ).val(),
    url = $form.attr( "action" );
​
  // Send the data using post
  var posting = $.post( url, { s: term } );
​
  // Put the results in a div
  posting.done(function( data ) {
    var content = $( data ).find( "#content" );
    $( "#result" ).empty().append( content );
  });
});
</script>
​
</body>
</html>
```
     */
    post(url: string,
         success_data: JQuery.jqXHR.DoneCallback | JQuery.PlainObject | string): JQuery.jqXHR;
    /**
     * Load data from the server using a HTTP POST request.
     * @param url_settings _&#x40;param_ `url_settings`
     * <br>
     * * `url` — A string containing the URL to which the request is sent. <br>
     * * `settings` — A set of key/value pairs that configure the Ajax request. All properties except for `url` are optional.
     *                A default can be set for any option with \`{@link ajaxSetup $.ajaxSetup()}\`. See \`{@link https://api.jquery.com/jquery.ajax/#jQuery-ajax-settings jQuery.ajax( settings )}\`
     *                for a complete list of all settings. Type will automatically be set to `POST`.
     * @see \`{@link https://api.jquery.com/jQuery.post/ }\`
     * @since 1.0
     * @since 1.12
     * @since 2.2
     * @example ​ ````Request the test.php page, but ignore the return results.
```javascript
$.post( "test.php" );
```
     */
    post(url_settings?: string | JQuery.UrlAjaxSettings): JQuery.jqXHR;

    // region proxy
    // #region proxy

    // region (funсtion, null | undefined)
    // #region (funсtion, null | undefined)

    // region 0 to 7 additional arguments
    // #region 0 to 7 additional arguments

    // region 0 parameters
    // #region 0 parameters

    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @param b An argument to be passed to the function referenced in the `function` argument.
     * @param c An argument to be passed to the function referenced in the `function` argument.
     * @param d An argument to be passed to the function referenced in the `function` argument.
     * @param e An argument to be passed to the function referenced in the `function` argument.
     * @param f An argument to be passed to the function referenced in the `function` argument.
     * @param g An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.9
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     */
    proxy<TReturn,
        A, B, C, D, E, F, G>(funсtion: (a: A, b: B, c: C, d: D, e: E, f: F, g: G) => TReturn,
                             context: null | undefined,
                             a: A, b: B, c: C, d: D, e: E, f: F, g: G): () => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @param b An argument to be passed to the function referenced in the `function` argument.
     * @param c An argument to be passed to the function referenced in the `function` argument.
     * @param d An argument to be passed to the function referenced in the `function` argument.
     * @param e An argument to be passed to the function referenced in the `function` argument.
     * @param f An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.9
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     */
    proxy<TReturn,
        A, B, C, D, E, F>(funсtion: (a: A, b: B, c: C, d: D, e: E, f: F) => TReturn,
                          context: null | undefined,
                          a: A, b: B, c: C, d: D, e: E, f: F): () => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @param b An argument to be passed to the function referenced in the `function` argument.
     * @param c An argument to be passed to the function referenced in the `function` argument.
     * @param d An argument to be passed to the function referenced in the `function` argument.
     * @param e An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.9
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     */
    proxy<TReturn,
        A, B, C, D, E>(funсtion: (a: A, b: B, c: C, d: D, e: E) => TReturn,
                       context: null | undefined,
                       a: A, b: B, c: C, d: D, e: E): () => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @param b An argument to be passed to the function referenced in the `function` argument.
     * @param c An argument to be passed to the function referenced in the `function` argument.
     * @param d An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.9
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     */
    proxy<TReturn,
        A, B, C, D>(funсtion: (a: A, b: B, c: C, d: D) => TReturn,
                    context: null | undefined,
                    a: A, b: B, c: C, d: D): () => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @param b An argument to be passed to the function referenced in the `function` argument.
     * @param c An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.9
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     */
    proxy<TReturn,
        A, B, C>(funсtion: (a: A, b: B, c: C) => TReturn,
                 context: null | undefined,
                 a: A, b: B, c: C): () => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @param b An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.9
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     */
    proxy<TReturn,
        A, B>(funсtion: (a: A, b: B) => TReturn,
              context: null | undefined,
              a: A, b: B): () => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.9
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     */
    proxy<TReturn,
        A>(funсtion: (a: A) => TReturn,
           context: null | undefined,
           a: A): () => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.9
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     */
    proxy<TReturn>(funсtion: () => TReturn,
                   context: null | undefined): () => TReturn;

    // #endregion

    // region 1 parameters
    // #region 1 parameters

    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @param b An argument to be passed to the function referenced in the `function` argument.
     * @param c An argument to be passed to the function referenced in the `function` argument.
     * @param d An argument to be passed to the function referenced in the `function` argument.
     * @param e An argument to be passed to the function referenced in the `function` argument.
     * @param f An argument to be passed to the function referenced in the `function` argument.
     * @param g An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.9
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     */
    proxy<TReturn,
        A, B, C, D, E, F, G,
        T>(funсtion: (a: A, b: B, c: C, d: D, e: E, f: F, g: G,
                      t: T) => TReturn,
           context: null | undefined,
           a: A, b: B, c: C, d: D, e: E, f: F, g: G): (t: T) => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @param b An argument to be passed to the function referenced in the `function` argument.
     * @param c An argument to be passed to the function referenced in the `function` argument.
     * @param d An argument to be passed to the function referenced in the `function` argument.
     * @param e An argument to be passed to the function referenced in the `function` argument.
     * @param f An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.9
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     */
    proxy<TReturn,
        A, B, C, D, E, F,
        T>(funсtion: (a: A, b: B, c: C, d: D, e: E, f: F,
                      t: T) => TReturn,
           context: null | undefined,
           a: A, b: B, c: C, d: D, e: E, f: F): (t: T) => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @param b An argument to be passed to the function referenced in the `function` argument.
     * @param c An argument to be passed to the function referenced in the `function` argument.
     * @param d An argument to be passed to the function referenced in the `function` argument.
     * @param e An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.9
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     */
    proxy<TReturn,
        A, B, C, D, E,
        T>(funсtion: (a: A, b: B, c: C, d: D, e: E,
                      t: T) => TReturn,
           context: null | undefined,
           a: A, b: B, c: C, d: D, e: E): (t: T) => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @param b An argument to be passed to the function referenced in the `function` argument.
     * @param c An argument to be passed to the function referenced in the `function` argument.
     * @param d An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.9
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     */
    proxy<TReturn,
        A, B, C, D,
        T>(funсtion: (a: A, b: B, c: C, d: D,
                      t: T) => TReturn,
           context: null | undefined,
           a: A, b: B, c: C, d: D): (t: T) => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @param b An argument to be passed to the function referenced in the `function` argument.
     * @param c An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.9
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     */
    proxy<TReturn,
        A, B, C,
        T>(funсtion: (a: A, b: B, c: C,
                      t: T) => TReturn,
           context: null | undefined,
           a: A, b: B, c: C): (t: T) => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @param b An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.9
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     */
    proxy<TReturn,
        A, B,
        T>(funсtion: (a: A, b: B,
                      t: T) => TReturn,
           context: null | undefined,
           a: A, b: B): (t: T) => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.9
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     */
    proxy<TReturn,
        A,
        T>(funсtion: (a: A,
                      t: T) => TReturn,
           context: null | undefined,
           a: A): (t: T) => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.9
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     */
    proxy<TReturn,
        T>(funсtion: (t: T) => TReturn,
           context: null | undefined): (t: T) => TReturn;

    // #endregion

    // region 2 parameters
    // #region 2 parameters

    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @param b An argument to be passed to the function referenced in the `function` argument.
     * @param c An argument to be passed to the function referenced in the `function` argument.
     * @param d An argument to be passed to the function referenced in the `function` argument.
     * @param e An argument to be passed to the function referenced in the `function` argument.
     * @param f An argument to be passed to the function referenced in the `function` argument.
     * @param g An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.9
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     */
    proxy<TReturn,
        A, B, C, D, E, F, G,
        T, U>(funсtion: (a: A, b: B, c: C, d: D, e: E, f: F, g: G,
                         t: T, u: U) => TReturn,
              context: null | undefined,
              a: A, b: B, c: C, d: D, e: E, f: F, g: G): (t: T, u: U) => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @param b An argument to be passed to the function referenced in the `function` argument.
     * @param c An argument to be passed to the function referenced in the `function` argument.
     * @param d An argument to be passed to the function referenced in the `function` argument.
     * @param e An argument to be passed to the function referenced in the `function` argument.
     * @param f An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.9
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     */
    proxy<TReturn,
        A, B, C, D, E, F,
        T, U>(funсtion: (a: A, b: B, c: C, d: D, e: E, f: F,
                         t: T, u: U) => TReturn,
              context: null | undefined,
              a: A, b: B, c: C, d: D, e: E, f: F): (t: T, u: U) => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @param b An argument to be passed to the function referenced in the `function` argument.
     * @param c An argument to be passed to the function referenced in the `function` argument.
     * @param d An argument to be passed to the function referenced in the `function` argument.
     * @param e An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.9
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     */
    proxy<TReturn,
        A, B, C, D, E,
        T, U>(funсtion: (a: A, b: B, c: C, d: D, e: E,
                         t: T, u: U) => TReturn,
              context: null | undefined,
              a: A, b: B, c: C, d: D, e: E): (t: T, u: U) => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @param b An argument to be passed to the function referenced in the `function` argument.
     * @param c An argument to be passed to the function referenced in the `function` argument.
     * @param d An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.9
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     */
    proxy<TReturn,
        A, B, C, D,
        T, U>(funсtion: (a: A, b: B, c: C, d: D,
                         t: T, u: U) => TReturn,
              context: null | undefined,
              a: A, b: B, c: C, d: D): (t: T, u: U) => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @param b An argument to be passed to the function referenced in the `function` argument.
     * @param c An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.9
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     */
    proxy<TReturn,
        A, B, C,
        T, U>(funсtion: (a: A, b: B, c: C,
                         t: T, u: U) => TReturn,
              context: null | undefined,
              a: A, b: B, c: C): (t: T, u: U) => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @param b An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.9
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     */
    proxy<TReturn,
        A, B,
        T, U>(funсtion: (a: A, b: B,
                         t: T, u: U) => TReturn,
              context: null | undefined,
              a: A, b: B): (t: T, u: U) => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.9
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     */
    proxy<TReturn,
        A,
        T, U>(funсtion: (a: A,
                         t: T, u: U) => TReturn,
              context: null | undefined,
              a: A): (t: T, u: U) => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.9
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     */
    proxy<TReturn,
        T, U>(funсtion: (t: T, u: U) => TReturn,
              context: null | undefined): (t: T, u: U) => TReturn;

    // #endregion

    // region 3 parameters
    // #region 3 parameters

    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @param b An argument to be passed to the function referenced in the `function` argument.
     * @param c An argument to be passed to the function referenced in the `function` argument.
     * @param d An argument to be passed to the function referenced in the `function` argument.
     * @param e An argument to be passed to the function referenced in the `function` argument.
     * @param f An argument to be passed to the function referenced in the `function` argument.
     * @param g An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.9
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     */
    proxy<TReturn,
        A, B, C, D, E, F, G,
        T, U, V>(funсtion: (a: A, b: B, c: C, d: D, e: E, f: F, g: G,
                            t: T, u: U, v: V) => TReturn,
                 context: null | undefined,
                 a: A, b: B, c: C, d: D, e: E, f: F, g: G): (t: T, u: U, v: V) => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @param b An argument to be passed to the function referenced in the `function` argument.
     * @param c An argument to be passed to the function referenced in the `function` argument.
     * @param d An argument to be passed to the function referenced in the `function` argument.
     * @param e An argument to be passed to the function referenced in the `function` argument.
     * @param f An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.9
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     */
    proxy<TReturn,
        A, B, C, D, E, F,
        T, U, V>(funсtion: (a: A, b: B, c: C, d: D, e: E, f: F,
                            t: T, u: U, v: V) => TReturn,
                 context: null | undefined,
                 a: A, b: B, c: C, d: D, e: E, f: F): (t: T, u: U, v: V) => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @param b An argument to be passed to the function referenced in the `function` argument.
     * @param c An argument to be passed to the function referenced in the `function` argument.
     * @param d An argument to be passed to the function referenced in the `function` argument.
     * @param e An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.9
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     */
    proxy<TReturn,
        A, B, C, D, E,
        T, U, V>(funсtion: (a: A, b: B, c: C, d: D, e: E,
                            t: T, u: U, v: V) => TReturn,
                 context: null | undefined,
                 a: A, b: B, c: C, d: D, e: E): (t: T, u: U, v: V) => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @param b An argument to be passed to the function referenced in the `function` argument.
     * @param c An argument to be passed to the function referenced in the `function` argument.
     * @param d An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.9
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     */
    proxy<TReturn,
        A, B, C, D,
        T, U, V>(funсtion: (a: A, b: B, c: C, d: D,
                            t: T, u: U, v: V) => TReturn,
                 context: null | undefined,
                 a: A, b: B, c: C, d: D): (t: T, u: U, v: V) => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @param b An argument to be passed to the function referenced in the `function` argument.
     * @param c An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.9
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     */
    proxy<TReturn,
        A, B, C,
        T, U, V>(funсtion: (a: A, b: B, c: C,
                            t: T, u: U, v: V) => TReturn,
                 context: null | undefined,
                 a: A, b: B, c: C): (t: T, u: U, v: V) => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @param b An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.9
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     */
    proxy<TReturn,
        A, B,
        T, U, V>(funсtion: (a: A, b: B,
                            t: T, u: U, v: V) => TReturn,
                 context: null | undefined,
                 a: A, b: B): (t: T, u: U, v: V) => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.9
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     */
    proxy<TReturn,
        A,
        T, U, V>(funсtion: (a: A,
                            t: T, u: U, v: V) => TReturn,
                 context: null | undefined,
                 a: A): (t: T, u: U, v: V) => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.9
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     */
    proxy<TReturn,
        T, U, V>(funсtion: (t: T, u: U, v: V) => TReturn,
                 context: null | undefined): (t: T, u: U, v: V) => TReturn;

    // #endregion

    // region 4 parameters
    // #region 4 parameters

    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @param b An argument to be passed to the function referenced in the `function` argument.
     * @param c An argument to be passed to the function referenced in the `function` argument.
     * @param d An argument to be passed to the function referenced in the `function` argument.
     * @param e An argument to be passed to the function referenced in the `function` argument.
     * @param f An argument to be passed to the function referenced in the `function` argument.
     * @param g An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.9
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     */
    proxy<TReturn,
        A, B, C, D, E, F, G,
        T, U, V, W>(funсtion: (a: A, b: B, c: C, d: D, e: E, f: F, g: G,
                               t: T, u: U, v: V, w: W) => TReturn,
                    context: null | undefined,
                    a: A, b: B, c: C, d: D, e: E, f: F, g: G): (t: T, u: U, v: V, w: W) => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @param b An argument to be passed to the function referenced in the `function` argument.
     * @param c An argument to be passed to the function referenced in the `function` argument.
     * @param d An argument to be passed to the function referenced in the `function` argument.
     * @param e An argument to be passed to the function referenced in the `function` argument.
     * @param f An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.9
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     */
    proxy<TReturn,
        A, B, C, D, E, F,
        T, U, V, W>(funсtion: (a: A, b: B, c: C, d: D, e: E, f: F,
                               t: T, u: U, v: V, w: W) => TReturn,
                    context: null | undefined,
                    a: A, b: B, c: C, d: D, e: E, f: F): (t: T, u: U, v: V, w: W) => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @param b An argument to be passed to the function referenced in the `function` argument.
     * @param c An argument to be passed to the function referenced in the `function` argument.
     * @param d An argument to be passed to the function referenced in the `function` argument.
     * @param e An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.9
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     */
    proxy<TReturn,
        A, B, C, D, E,
        T, U, V, W>(funсtion: (a: A, b: B, c: C, d: D, e: E,
                               t: T, u: U, v: V, w: W) => TReturn,
                    context: null | undefined,
                    a: A, b: B, c: C, d: D, e: E): (t: T, u: U, v: V, w: W) => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @param b An argument to be passed to the function referenced in the `function` argument.
     * @param c An argument to be passed to the function referenced in the `function` argument.
     * @param d An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.9
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     */
    proxy<TReturn,
        A, B, C, D,
        T, U, V, W>(funсtion: (a: A, b: B, c: C, d: D,
                               t: T, u: U, v: V, w: W) => TReturn,
                    context: null | undefined,
                    a: A, b: B, c: C, d: D): (t: T, u: U, v: V, w: W) => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @param b An argument to be passed to the function referenced in the `function` argument.
     * @param c An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.9
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     */
    proxy<TReturn,
        A, B, C,
        T, U, V, W>(funсtion: (a: A, b: B, c: C,
                               t: T, u: U, v: V, w: W) => TReturn,
                    context: null | undefined,
                    a: A, b: B, c: C): (t: T, u: U, v: V, w: W) => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @param b An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.9
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     */
    proxy<TReturn,
        A, B,
        T, U, V, W>(funсtion: (a: A, b: B,
                               t: T, u: U, v: V, w: W) => TReturn,
                    context: null | undefined,
                    a: A, b: B): (t: T, u: U, v: V, w: W) => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.9
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     */
    proxy<TReturn,
        A,
        T, U, V, W>(funсtion: (a: A,
                               t: T, u: U, v: V, w: W) => TReturn,
                    context: null | undefined,
                    a: A): (t: T, u: U, v: V, w: W) => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.9
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     */
    proxy<TReturn,
        T, U, V, W>(funсtion: (t: T, u: U, v: V, w: W) => TReturn,
                    context: null | undefined): (t: T, u: U, v: V, w: W) => TReturn;

    // #endregion

    // region 5 parameters
    // #region 5 parameters

    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @param b An argument to be passed to the function referenced in the `function` argument.
     * @param c An argument to be passed to the function referenced in the `function` argument.
     * @param d An argument to be passed to the function referenced in the `function` argument.
     * @param e An argument to be passed to the function referenced in the `function` argument.
     * @param f An argument to be passed to the function referenced in the `function` argument.
     * @param g An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.9
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     */
    proxy<TReturn,
        A, B, C, D, E, F, G,
        T, U, V, W, X>(funсtion: (a: A, b: B, c: C, d: D, e: E, f: F, g: G,
                                  t: T, u: U, v: V, w: W, x: X) => TReturn,
                       context: null | undefined,
                       a: A, b: B, c: C, d: D, e: E, f: F, g: G): (t: T, u: U, v: V, w: W, x: X) => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @param b An argument to be passed to the function referenced in the `function` argument.
     * @param c An argument to be passed to the function referenced in the `function` argument.
     * @param d An argument to be passed to the function referenced in the `function` argument.
     * @param e An argument to be passed to the function referenced in the `function` argument.
     * @param f An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.9
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     */
    proxy<TReturn,
        A, B, C, D, E, F,
        T, U, V, W, X>(funсtion: (a: A, b: B, c: C, d: D, e: E, f: F,
                                  t: T, u: U, v: V, w: W, x: X) => TReturn,
                       context: null | undefined,
                       a: A, b: B, c: C, d: D, e: E, f: F): (t: T, u: U, v: V, w: W, x: X) => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @param b An argument to be passed to the function referenced in the `function` argument.
     * @param c An argument to be passed to the function referenced in the `function` argument.
     * @param d An argument to be passed to the function referenced in the `function` argument.
     * @param e An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.9
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     */
    proxy<TReturn,
        A, B, C, D, E,
        T, U, V, W, X>(funсtion: (a: A, b: B, c: C, d: D, e: E,
                                  t: T, u: U, v: V, w: W, x: X) => TReturn,
                       context: null | undefined,
                       a: A, b: B, c: C, d: D, e: E): (t: T, u: U, v: V, w: W, x: X) => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @param b An argument to be passed to the function referenced in the `function` argument.
     * @param c An argument to be passed to the function referenced in the `function` argument.
     * @param d An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.9
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     */
    proxy<TReturn,
        A, B, C, D,
        T, U, V, W, X>(funсtion: (a: A, b: B, c: C, d: D,
                                  t: T, u: U, v: V, w: W, x: X) => TReturn,
                       context: null | undefined,
                       a: A, b: B, c: C, d: D): (t: T, u: U, v: V, w: W, x: X) => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @param b An argument to be passed to the function referenced in the `function` argument.
     * @param c An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.9
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     */
    proxy<TReturn,
        A, B, C,
        T, U, V, W, X>(funсtion: (a: A, b: B, c: C,
                                  t: T, u: U, v: V, w: W, x: X) => TReturn,
                       context: null | undefined,
                       a: A, b: B, c: C): (t: T, u: U, v: V, w: W, x: X) => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @param b An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.9
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     */
    proxy<TReturn,
        A, B,
        T, U, V, W, X>(funсtion: (a: A, b: B,
                                  t: T, u: U, v: V, w: W, x: X) => TReturn,
                       context: null | undefined,
                       a: A, b: B): (t: T, u: U, v: V, w: W, x: X) => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.9
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     */
    proxy<TReturn,
        A,
        T, U, V, W, X>(funсtion: (a: A,
                                  t: T, u: U, v: V, w: W, x: X) => TReturn,
                       context: null | undefined,
                       a: A): (t: T, u: U, v: V, w: W, x: X) => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.9
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     */
    proxy<TReturn,
        T, U, V, W, X>(funсtion: (t: T, u: U, v: V, w: W, x: X) => TReturn,
                       context: null | undefined): (t: T, u: U, v: V, w: W, x: X) => TReturn;

    // #endregion

    // region 6 parameters
    // #region 6 parameters

    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @param b An argument to be passed to the function referenced in the `function` argument.
     * @param c An argument to be passed to the function referenced in the `function` argument.
     * @param d An argument to be passed to the function referenced in the `function` argument.
     * @param e An argument to be passed to the function referenced in the `function` argument.
     * @param f An argument to be passed to the function referenced in the `function` argument.
     * @param g An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.9
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     */
    proxy<TReturn,
        A, B, C, D, E, F, G,
        T, U, V, W, X, Y>(funсtion: (a: A, b: B, c: C, d: D, e: E, f: F, g: G,
                                     t: T, u: U, v: V, w: W, x: X, y: Y) => TReturn,
                          context: null | undefined,
                          a: A, b: B, c: C, d: D, e: E, f: F, g: G): (t: T, u: U, v: V, w: W, x: X, y: Y) => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @param b An argument to be passed to the function referenced in the `function` argument.
     * @param c An argument to be passed to the function referenced in the `function` argument.
     * @param d An argument to be passed to the function referenced in the `function` argument.
     * @param e An argument to be passed to the function referenced in the `function` argument.
     * @param f An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.9
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     */
    proxy<TReturn,
        A, B, C, D, E, F,
        T, U, V, W, X, Y>(funсtion: (a: A, b: B, c: C, d: D, e: E, f: F,
                                     t: T, u: U, v: V, w: W, x: X, y: Y) => TReturn,
                          context: null | undefined,
                          a: A, b: B, c: C, d: D, e: E, f: F): (t: T, u: U, v: V, w: W, x: X, y: Y) => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @param b An argument to be passed to the function referenced in the `function` argument.
     * @param c An argument to be passed to the function referenced in the `function` argument.
     * @param d An argument to be passed to the function referenced in the `function` argument.
     * @param e An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.9
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     */
    proxy<TReturn,
        A, B, C, D, E,
        T, U, V, W, X, Y>(funсtion: (a: A, b: B, c: C, d: D, e: E,
                                     t: T, u: U, v: V, w: W, x: X, y: Y) => TReturn,
                          context: null | undefined,
                          a: A, b: B, c: C, d: D, e: E): (t: T, u: U, v: V, w: W, x: X, y: Y) => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @param b An argument to be passed to the function referenced in the `function` argument.
     * @param c An argument to be passed to the function referenced in the `function` argument.
     * @param d An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.9
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     */
    proxy<TReturn,
        A, B, C, D,
        T, U, V, W, X, Y>(funсtion: (a: A, b: B, c: C, d: D,
                                     t: T, u: U, v: V, w: W, x: X, y: Y) => TReturn,
                          context: null | undefined,
                          a: A, b: B, c: C, d: D): (t: T, u: U, v: V, w: W, x: X, y: Y) => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @param b An argument to be passed to the function referenced in the `function` argument.
     * @param c An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.9
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     */
    proxy<TReturn,
        A, B, C,
        T, U, V, W, X, Y>(funсtion: (a: A, b: B, c: C,
                                     t: T, u: U, v: V, w: W, x: X, y: Y) => TReturn,
                          context: null | undefined,
                          a: A, b: B, c: C): (t: T, u: U, v: V, w: W, x: X, y: Y) => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @param b An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.9
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     */
    proxy<TReturn,
        A, B,
        T, U, V, W, X, Y>(funсtion: (a: A, b: B,
                                     t: T, u: U, v: V, w: W, x: X, y: Y) => TReturn,
                          context: null | undefined,
                          a: A, b: B): (t: T, u: U, v: V, w: W, x: X, y: Y) => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.9
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     */
    proxy<TReturn,
        A,
        T, U, V, W, X, Y>(funсtion: (a: A,
                                     t: T, u: U, v: V, w: W, x: X, y: Y) => TReturn,
                          context: null | undefined,
                          a: A): (t: T, u: U, v: V, w: W, x: X, y: Y) => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.9
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     */
    proxy<TReturn,
        T, U, V, W, X, Y>(funсtion: (t: T, u: U, v: V, w: W, x: X, y: Y) => TReturn,
                          context: null | undefined): (t: T, u: U, v: V, w: W, x: X, y: Y) => TReturn;

    // #endregion

    // region 7+ parameters
    // #region 7+ parameters

    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @param b An argument to be passed to the function referenced in the `function` argument.
     * @param c An argument to be passed to the function referenced in the `function` argument.
     * @param d An argument to be passed to the function referenced in the `function` argument.
     * @param e An argument to be passed to the function referenced in the `function` argument.
     * @param f An argument to be passed to the function referenced in the `function` argument.
     * @param g An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.9
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     */
    proxy<TReturn,
        A, B, C, D, E, F, G,
        T, U, V, W, X, Y, Z>(funсtion: (a: A, b: B, c: C, d: D, e: E, f: F, g: G,
                                        t: T, u: U, v: V, w: W, x: X, y: Y, z: Z, ...args: any[]) => TReturn,
                             context: null | undefined,
                             a: A, b: B, c: C, d: D, e: E, f: F, g: G): (t: T, u: U, v: V, w: W, x: X, y: Y, z: Z, ...args: any[]) => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @param b An argument to be passed to the function referenced in the `function` argument.
     * @param c An argument to be passed to the function referenced in the `function` argument.
     * @param d An argument to be passed to the function referenced in the `function` argument.
     * @param e An argument to be passed to the function referenced in the `function` argument.
     * @param f An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.9
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     */
    proxy<TReturn,
        A, B, C, D, E, F,
        T, U, V, W, X, Y, Z>(funсtion: (a: A, b: B, c: C, d: D, e: E, f: F,
                                        t: T, u: U, v: V, w: W, x: X, y: Y, z: Z, ...args: any[]) => TReturn,
                             context: null | undefined,
                             a: A, b: B, c: C, d: D, e: E, f: F): (t: T, u: U, v: V, w: W, x: X, y: Y, z: Z, ...args: any[]) => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @param b An argument to be passed to the function referenced in the `function` argument.
     * @param c An argument to be passed to the function referenced in the `function` argument.
     * @param d An argument to be passed to the function referenced in the `function` argument.
     * @param e An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.9
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     */
    proxy<TReturn,
        A, B, C, D, E,
        T, U, V, W, X, Y, Z>(funсtion: (a: A, b: B, c: C, d: D, e: E,
                                        t: T, u: U, v: V, w: W, x: X, y: Y, z: Z, ...args: any[]) => TReturn,
                             context: null | undefined,
                             a: A, b: B, c: C, d: D, e: E): (t: T, u: U, v: V, w: W, x: X, y: Y, z: Z, ...args: any[]) => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @param b An argument to be passed to the function referenced in the `function` argument.
     * @param c An argument to be passed to the function referenced in the `function` argument.
     * @param d An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.9
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     */
    proxy<TReturn,
        A, B, C, D,
        T, U, V, W, X, Y, Z>(funсtion: (a: A, b: B, c: C, d: D,
                                        t: T, u: U, v: V, w: W, x: X, y: Y, z: Z, ...args: any[]) => TReturn,
                             context: null | undefined,
                             a: A, b: B, c: C, d: D): (t: T, u: U, v: V, w: W, x: X, y: Y, z: Z, ...args: any[]) => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @param b An argument to be passed to the function referenced in the `function` argument.
     * @param c An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.9
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     */
    proxy<TReturn,
        A, B, C,
        T, U, V, W, X, Y, Z>(funсtion: (a: A, b: B, c: C,
                                        t: T, u: U, v: V, w: W, x: X, y: Y, z: Z, ...args: any[]) => TReturn,
                             context: null | undefined,
                             a: A, b: B, c: C): (t: T, u: U, v: V, w: W, x: X, y: Y, z: Z, ...args: any[]) => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @param b An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.9
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     */
    proxy<TReturn,
        A, B,
        T, U, V, W, X, Y, Z>(funсtion: (a: A, b: B,
                                        t: T, u: U, v: V, w: W, x: X, y: Y, z: Z, ...args: any[]) => TReturn,
                             context: null | undefined,
                             a: A, b: B): (t: T, u: U, v: V, w: W, x: X, y: Y, z: Z, ...args: any[]) => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.9
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     */
    proxy<TReturn,
        A,
        T, U, V, W, X, Y, Z>(funсtion: (a: A,
                                        t: T, u: U, v: V, w: W, x: X, y: Y, z: Z, ...args: any[]) => TReturn,
                             context: null | undefined,
                             a: A): (t: T, u: U, v: V, w: W, x: X, y: Y, z: Z, ...args: any[]) => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.9
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     */
    proxy<TReturn,
        T, U, V, W, X, Y, Z>(funсtion: (t: T, u: U, v: V, w: W, x: X, y: Y, z: Z, ...args: any[]) => TReturn,
                             context: null | undefined): (t: T, u: U, v: V, w: W, x: X, y: Y, z: Z, ...args: any[]) => TReturn;

    // #endregion

    // #endregion

    // region 8+ additional arguments
    // #region 8+ additional arguments

    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param additionalArguments Any number of arguments to be passed to the function referenced in the function argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.9
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     */
    proxy<TReturn>(funсtion: (...args: any[]) => TReturn,
                   context: null | undefined,
                   ...additionalArguments: any[]): (...args: any[]) => TReturn;

    // #endregion

    // #endregion

    // region (funсtion, context)
    // #region (funсtion, context)

    // region 0 to 7 additional arguments
    // #region 0 to 7 additional arguments

    // region 0 parameters
    // #region 0 parameters

    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @param b An argument to be passed to the function referenced in the `function` argument.
     * @param c An argument to be passed to the function referenced in the `function` argument.
     * @param d An argument to be passed to the function referenced in the `function` argument.
     * @param e An argument to be passed to the function referenced in the `function` argument.
     * @param f An argument to be passed to the function referenced in the `function` argument.
     * @param g An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.4
     * @since 1.6
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     * @example ​ ````Change the context of functions bound to a click handler using the &quot;function, context&quot; signature. Unbind the first handler after first click.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  type: "zombie",
  test: function( event ) {
    // Without proxy, `this` would refer to the event target
    // use event.target to reference that element.
    var element = event.target;
    $( element ).css( "background-color", "red" );
​
    // With proxy, `this` refers to the me object encapsulating
    // this function.
    $( "#log" ).append( "Hello " + this.type + "<br>" );
    $( "#test" ).off( "click", this.test );
  }
};
​
var you = {
  type: "person",
  test: function( event ) {
    $( "#log" ).append( this.type + " " );
  }
};
​
// Execute you.test() in the context of the `you` object
// no matter where it is called
// i.e. the `this` keyword will refer to `you`
var youClick = $.proxy( you.test, you );
​
// attach click handlers to #test
$( "#test" )
  // this === "zombie"; handler unbound after first click
  .on( "click", $.proxy( me.test, me ) )
​
  // this === "person"
  .on( "click", youClick )
​
  // this === "zombie"
  .on( "click", $.proxy( you.test, me ) )
​
  // this === "<button> element"
  .on( "click", you.test );
</script>
​
</body>
</html>
```
     * @example ​ ````Change the context of a function bound to the click handler,
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  // I'm a dog
  type: "dog",
​
  // Note that event comes *after* one and two
  test: function( one, two, event ) {
    $( "#log" )
​
      // `one` maps to `you`, the 1st additional
      // argument in the $.proxy function call
      .append( "<h3>Hello " + one.type + ":</h3>" )
​
      // The `this` keyword refers to `me`
      // (the 2nd, context, argument of $.proxy)
      .append( "I am a " + this.type + ", " )
​
      // `two` maps to `they`, the 2nd additional
      // argument in the $.proxy function call
      .append( "and they are " + two.type + ".<br>" )
​
      // The event type is "click"
      .append( "Thanks for " + event.type + "ing." )
​
      // The clicked element is `event.target`,
      // and its type is "button"
      .append( "the " + event.target.type + "." );
  }
};
​
var you = { type: "cat" };
var they = { type: "fish" };
​
// Set up handler to execute me.test() in the context
// of `me`, with `you` and `they` as additional arguments
var proxy = $.proxy( me.test, me, you, they );
​
$( "#test" )
  .on( "click", proxy );
</script>
​
</body>
</html>
```
     */
    proxy<TContext,
        TReturn,
        A, B, C, D, E, F, G>(funсtion: (this: TContext, a: A, b: B, c: C, d: D, e: E, f: F, g: G) => TReturn,
                             context: TContext,
                             a: A, b: B, c: C, d: D, e: E, f: F, g: G): () => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @param b An argument to be passed to the function referenced in the `function` argument.
     * @param c An argument to be passed to the function referenced in the `function` argument.
     * @param d An argument to be passed to the function referenced in the `function` argument.
     * @param e An argument to be passed to the function referenced in the `function` argument.
     * @param f An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.4
     * @since 1.6
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     * @example ​ ````Change the context of functions bound to a click handler using the &quot;function, context&quot; signature. Unbind the first handler after first click.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  type: "zombie",
  test: function( event ) {
    // Without proxy, `this` would refer to the event target
    // use event.target to reference that element.
    var element = event.target;
    $( element ).css( "background-color", "red" );
​
    // With proxy, `this` refers to the me object encapsulating
    // this function.
    $( "#log" ).append( "Hello " + this.type + "<br>" );
    $( "#test" ).off( "click", this.test );
  }
};
​
var you = {
  type: "person",
  test: function( event ) {
    $( "#log" ).append( this.type + " " );
  }
};
​
// Execute you.test() in the context of the `you` object
// no matter where it is called
// i.e. the `this` keyword will refer to `you`
var youClick = $.proxy( you.test, you );
​
// attach click handlers to #test
$( "#test" )
  // this === "zombie"; handler unbound after first click
  .on( "click", $.proxy( me.test, me ) )
​
  // this === "person"
  .on( "click", youClick )
​
  // this === "zombie"
  .on( "click", $.proxy( you.test, me ) )
​
  // this === "<button> element"
  .on( "click", you.test );
</script>
​
</body>
</html>
```
     * @example ​ ````Change the context of a function bound to the click handler,
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  // I'm a dog
  type: "dog",
​
  // Note that event comes *after* one and two
  test: function( one, two, event ) {
    $( "#log" )
​
      // `one` maps to `you`, the 1st additional
      // argument in the $.proxy function call
      .append( "<h3>Hello " + one.type + ":</h3>" )
​
      // The `this` keyword refers to `me`
      // (the 2nd, context, argument of $.proxy)
      .append( "I am a " + this.type + ", " )
​
      // `two` maps to `they`, the 2nd additional
      // argument in the $.proxy function call
      .append( "and they are " + two.type + ".<br>" )
​
      // The event type is "click"
      .append( "Thanks for " + event.type + "ing." )
​
      // The clicked element is `event.target`,
      // and its type is "button"
      .append( "the " + event.target.type + "." );
  }
};
​
var you = { type: "cat" };
var they = { type: "fish" };
​
// Set up handler to execute me.test() in the context
// of `me`, with `you` and `they` as additional arguments
var proxy = $.proxy( me.test, me, you, they );
​
$( "#test" )
  .on( "click", proxy );
</script>
​
</body>
</html>
```
     */
    proxy<TContext,
        TReturn,
        A, B, C, D, E, F>(funсtion: (this: TContext, a: A, b: B, c: C, d: D, e: E, f: F) => TReturn,
                          context: TContext,
                          a: A, b: B, c: C, d: D, e: E, f: F): () => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @param b An argument to be passed to the function referenced in the `function` argument.
     * @param c An argument to be passed to the function referenced in the `function` argument.
     * @param d An argument to be passed to the function referenced in the `function` argument.
     * @param e An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.4
     * @since 1.6
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     * @example ​ ````Change the context of functions bound to a click handler using the &quot;function, context&quot; signature. Unbind the first handler after first click.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  type: "zombie",
  test: function( event ) {
    // Without proxy, `this` would refer to the event target
    // use event.target to reference that element.
    var element = event.target;
    $( element ).css( "background-color", "red" );
​
    // With proxy, `this` refers to the me object encapsulating
    // this function.
    $( "#log" ).append( "Hello " + this.type + "<br>" );
    $( "#test" ).off( "click", this.test );
  }
};
​
var you = {
  type: "person",
  test: function( event ) {
    $( "#log" ).append( this.type + " " );
  }
};
​
// Execute you.test() in the context of the `you` object
// no matter where it is called
// i.e. the `this` keyword will refer to `you`
var youClick = $.proxy( you.test, you );
​
// attach click handlers to #test
$( "#test" )
  // this === "zombie"; handler unbound after first click
  .on( "click", $.proxy( me.test, me ) )
​
  // this === "person"
  .on( "click", youClick )
​
  // this === "zombie"
  .on( "click", $.proxy( you.test, me ) )
​
  // this === "<button> element"
  .on( "click", you.test );
</script>
​
</body>
</html>
```
     * @example ​ ````Change the context of a function bound to the click handler,
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  // I'm a dog
  type: "dog",
​
  // Note that event comes *after* one and two
  test: function( one, two, event ) {
    $( "#log" )
​
      // `one` maps to `you`, the 1st additional
      // argument in the $.proxy function call
      .append( "<h3>Hello " + one.type + ":</h3>" )
​
      // The `this` keyword refers to `me`
      // (the 2nd, context, argument of $.proxy)
      .append( "I am a " + this.type + ", " )
​
      // `two` maps to `they`, the 2nd additional
      // argument in the $.proxy function call
      .append( "and they are " + two.type + ".<br>" )
​
      // The event type is "click"
      .append( "Thanks for " + event.type + "ing." )
​
      // The clicked element is `event.target`,
      // and its type is "button"
      .append( "the " + event.target.type + "." );
  }
};
​
var you = { type: "cat" };
var they = { type: "fish" };
​
// Set up handler to execute me.test() in the context
// of `me`, with `you` and `they` as additional arguments
var proxy = $.proxy( me.test, me, you, they );
​
$( "#test" )
  .on( "click", proxy );
</script>
​
</body>
</html>
```
     */
    proxy<TContext,
        TReturn,
        A, B, C, D, E>(funсtion: (this: TContext, a: A, b: B, c: C, d: D, e: E) => TReturn,
                       context: TContext,
                       a: A, b: B, c: C, d: D, e: E): () => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @param b An argument to be passed to the function referenced in the `function` argument.
     * @param c An argument to be passed to the function referenced in the `function` argument.
     * @param d An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.4
     * @since 1.6
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     * @example ​ ````Change the context of functions bound to a click handler using the &quot;function, context&quot; signature. Unbind the first handler after first click.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  type: "zombie",
  test: function( event ) {
    // Without proxy, `this` would refer to the event target
    // use event.target to reference that element.
    var element = event.target;
    $( element ).css( "background-color", "red" );
​
    // With proxy, `this` refers to the me object encapsulating
    // this function.
    $( "#log" ).append( "Hello " + this.type + "<br>" );
    $( "#test" ).off( "click", this.test );
  }
};
​
var you = {
  type: "person",
  test: function( event ) {
    $( "#log" ).append( this.type + " " );
  }
};
​
// Execute you.test() in the context of the `you` object
// no matter where it is called
// i.e. the `this` keyword will refer to `you`
var youClick = $.proxy( you.test, you );
​
// attach click handlers to #test
$( "#test" )
  // this === "zombie"; handler unbound after first click
  .on( "click", $.proxy( me.test, me ) )
​
  // this === "person"
  .on( "click", youClick )
​
  // this === "zombie"
  .on( "click", $.proxy( you.test, me ) )
​
  // this === "<button> element"
  .on( "click", you.test );
</script>
​
</body>
</html>
```
     * @example ​ ````Change the context of a function bound to the click handler,
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  // I'm a dog
  type: "dog",
​
  // Note that event comes *after* one and two
  test: function( one, two, event ) {
    $( "#log" )
​
      // `one` maps to `you`, the 1st additional
      // argument in the $.proxy function call
      .append( "<h3>Hello " + one.type + ":</h3>" )
​
      // The `this` keyword refers to `me`
      // (the 2nd, context, argument of $.proxy)
      .append( "I am a " + this.type + ", " )
​
      // `two` maps to `they`, the 2nd additional
      // argument in the $.proxy function call
      .append( "and they are " + two.type + ".<br>" )
​
      // The event type is "click"
      .append( "Thanks for " + event.type + "ing." )
​
      // The clicked element is `event.target`,
      // and its type is "button"
      .append( "the " + event.target.type + "." );
  }
};
​
var you = { type: "cat" };
var they = { type: "fish" };
​
// Set up handler to execute me.test() in the context
// of `me`, with `you` and `they` as additional arguments
var proxy = $.proxy( me.test, me, you, they );
​
$( "#test" )
  .on( "click", proxy );
</script>
​
</body>
</html>
```
     */
    proxy<TContext,
        TReturn,
        A, B, C, D>(funсtion: (this: TContext, a: A, b: B, c: C, d: D) => TReturn,
                    context: TContext,
                    a: A, b: B, c: C, d: D): () => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @param b An argument to be passed to the function referenced in the `function` argument.
     * @param c An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.4
     * @since 1.6
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     * @example ​ ````Change the context of functions bound to a click handler using the &quot;function, context&quot; signature. Unbind the first handler after first click.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  type: "zombie",
  test: function( event ) {
    // Without proxy, `this` would refer to the event target
    // use event.target to reference that element.
    var element = event.target;
    $( element ).css( "background-color", "red" );
​
    // With proxy, `this` refers to the me object encapsulating
    // this function.
    $( "#log" ).append( "Hello " + this.type + "<br>" );
    $( "#test" ).off( "click", this.test );
  }
};
​
var you = {
  type: "person",
  test: function( event ) {
    $( "#log" ).append( this.type + " " );
  }
};
​
// Execute you.test() in the context of the `you` object
// no matter where it is called
// i.e. the `this` keyword will refer to `you`
var youClick = $.proxy( you.test, you );
​
// attach click handlers to #test
$( "#test" )
  // this === "zombie"; handler unbound after first click
  .on( "click", $.proxy( me.test, me ) )
​
  // this === "person"
  .on( "click", youClick )
​
  // this === "zombie"
  .on( "click", $.proxy( you.test, me ) )
​
  // this === "<button> element"
  .on( "click", you.test );
</script>
​
</body>
</html>
```
     * @example ​ ````Change the context of a function bound to the click handler,
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  // I'm a dog
  type: "dog",
​
  // Note that event comes *after* one and two
  test: function( one, two, event ) {
    $( "#log" )
​
      // `one` maps to `you`, the 1st additional
      // argument in the $.proxy function call
      .append( "<h3>Hello " + one.type + ":</h3>" )
​
      // The `this` keyword refers to `me`
      // (the 2nd, context, argument of $.proxy)
      .append( "I am a " + this.type + ", " )
​
      // `two` maps to `they`, the 2nd additional
      // argument in the $.proxy function call
      .append( "and they are " + two.type + ".<br>" )
​
      // The event type is "click"
      .append( "Thanks for " + event.type + "ing." )
​
      // The clicked element is `event.target`,
      // and its type is "button"
      .append( "the " + event.target.type + "." );
  }
};
​
var you = { type: "cat" };
var they = { type: "fish" };
​
// Set up handler to execute me.test() in the context
// of `me`, with `you` and `they` as additional arguments
var proxy = $.proxy( me.test, me, you, they );
​
$( "#test" )
  .on( "click", proxy );
</script>
​
</body>
</html>
```
     */
    proxy<TContext,
        TReturn,
        A, B, C>(funсtion: (this: TContext, a: A, b: B, c: C) => TReturn,
                 context: TContext,
                 a: A, b: B, c: C): () => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @param b An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.4
     * @since 1.6
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     * @example ​ ````Change the context of functions bound to a click handler using the &quot;function, context&quot; signature. Unbind the first handler after first click.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  type: "zombie",
  test: function( event ) {
    // Without proxy, `this` would refer to the event target
    // use event.target to reference that element.
    var element = event.target;
    $( element ).css( "background-color", "red" );
​
    // With proxy, `this` refers to the me object encapsulating
    // this function.
    $( "#log" ).append( "Hello " + this.type + "<br>" );
    $( "#test" ).off( "click", this.test );
  }
};
​
var you = {
  type: "person",
  test: function( event ) {
    $( "#log" ).append( this.type + " " );
  }
};
​
// Execute you.test() in the context of the `you` object
// no matter where it is called
// i.e. the `this` keyword will refer to `you`
var youClick = $.proxy( you.test, you );
​
// attach click handlers to #test
$( "#test" )
  // this === "zombie"; handler unbound after first click
  .on( "click", $.proxy( me.test, me ) )
​
  // this === "person"
  .on( "click", youClick )
​
  // this === "zombie"
  .on( "click", $.proxy( you.test, me ) )
​
  // this === "<button> element"
  .on( "click", you.test );
</script>
​
</body>
</html>
```
     * @example ​ ````Change the context of a function bound to the click handler,
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  // I'm a dog
  type: "dog",
​
  // Note that event comes *after* one and two
  test: function( one, two, event ) {
    $( "#log" )
​
      // `one` maps to `you`, the 1st additional
      // argument in the $.proxy function call
      .append( "<h3>Hello " + one.type + ":</h3>" )
​
      // The `this` keyword refers to `me`
      // (the 2nd, context, argument of $.proxy)
      .append( "I am a " + this.type + ", " )
​
      // `two` maps to `they`, the 2nd additional
      // argument in the $.proxy function call
      .append( "and they are " + two.type + ".<br>" )
​
      // The event type is "click"
      .append( "Thanks for " + event.type + "ing." )
​
      // The clicked element is `event.target`,
      // and its type is "button"
      .append( "the " + event.target.type + "." );
  }
};
​
var you = { type: "cat" };
var they = { type: "fish" };
​
// Set up handler to execute me.test() in the context
// of `me`, with `you` and `they` as additional arguments
var proxy = $.proxy( me.test, me, you, they );
​
$( "#test" )
  .on( "click", proxy );
</script>
​
</body>
</html>
```
     */
    proxy<TContext,
        TReturn,
        A, B>(funсtion: (this: TContext, a: A, b: B) => TReturn,
              context: TContext,
              a: A, b: B): () => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.4`
     * @since 1.6
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     * @example ​ ````Change the context of functions bound to a click handler using the &quot;function, context&quot; signature. Unbind the first handler after first click.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  type: "zombie",
  test: function( event ) {
    // Without proxy, `this` would refer to the event target
    // use event.target to reference that element.
    var element = event.target;
    $( element ).css( "background-color", "red" );
​
    // With proxy, `this` refers to the me object encapsulating
    // this function.
    $( "#log" ).append( "Hello " + this.type + "<br>" );
    $( "#test" ).off( "click", this.test );
  }
};
​
var you = {
  type: "person",
  test: function( event ) {
    $( "#log" ).append( this.type + " " );
  }
};
​
// Execute you.test() in the context of the `you` object
// no matter where it is called
// i.e. the `this` keyword will refer to `you`
var youClick = $.proxy( you.test, you );
​
// attach click handlers to #test
$( "#test" )
  // this === "zombie"; handler unbound after first click
  .on( "click", $.proxy( me.test, me ) )
​
  // this === "person"
  .on( "click", youClick )
​
  // this === "zombie"
  .on( "click", $.proxy( you.test, me ) )
​
  // this === "<button> element"
  .on( "click", you.test );
</script>
​
</body>
</html>
```
     * @example ​ ````Change the context of a function bound to the click handler,
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  // I'm a dog
  type: "dog",
​
  // Note that event comes *after* one and two
  test: function( one, two, event ) {
    $( "#log" )
​
      // `one` maps to `you`, the 1st additional
      // argument in the $.proxy function call
      .append( "<h3>Hello " + one.type + ":</h3>" )
​
      // The `this` keyword refers to `me`
      // (the 2nd, context, argument of $.proxy)
      .append( "I am a " + this.type + ", " )
​
      // `two` maps to `they`, the 2nd additional
      // argument in the $.proxy function call
      .append( "and they are " + two.type + ".<br>" )
​
      // The event type is "click"
      .append( "Thanks for " + event.type + "ing." )
​
      // The clicked element is `event.target`,
      // and its type is "button"
      .append( "the " + event.target.type + "." );
  }
};
​
var you = { type: "cat" };
var they = { type: "fish" };
​
// Set up handler to execute me.test() in the context
// of `me`, with `you` and `they` as additional arguments
var proxy = $.proxy( me.test, me, you, they );
​
$( "#test" )
  .on( "click", proxy );
</script>
​
</body>
</html>
```
     */
    proxy<TContext,
        TReturn,
        A>(funсtion: (this: TContext, a: A) => TReturn,
           context: TContext,
           a: A): () => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.4
     * @since 1.6
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     * @example ​ ````Change the context of functions bound to a click handler using the &quot;function, context&quot; signature. Unbind the first handler after first click.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  type: "zombie",
  test: function( event ) {
    // Without proxy, `this` would refer to the event target
    // use event.target to reference that element.
    var element = event.target;
    $( element ).css( "background-color", "red" );
​
    // With proxy, `this` refers to the me object encapsulating
    // this function.
    $( "#log" ).append( "Hello " + this.type + "<br>" );
    $( "#test" ).off( "click", this.test );
  }
};
​
var you = {
  type: "person",
  test: function( event ) {
    $( "#log" ).append( this.type + " " );
  }
};
​
// Execute you.test() in the context of the `you` object
// no matter where it is called
// i.e. the `this` keyword will refer to `you`
var youClick = $.proxy( you.test, you );
​
// attach click handlers to #test
$( "#test" )
  // this === "zombie"; handler unbound after first click
  .on( "click", $.proxy( me.test, me ) )
​
  // this === "person"
  .on( "click", youClick )
​
  // this === "zombie"
  .on( "click", $.proxy( you.test, me ) )
​
  // this === "<button> element"
  .on( "click", you.test );
</script>
​
</body>
</html>
```
     * @example ​ ````Change the context of a function bound to the click handler,
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  // I'm a dog
  type: "dog",
​
  // Note that event comes *after* one and two
  test: function( one, two, event ) {
    $( "#log" )
​
      // `one` maps to `you`, the 1st additional
      // argument in the $.proxy function call
      .append( "<h3>Hello " + one.type + ":</h3>" )
​
      // The `this` keyword refers to `me`
      // (the 2nd, context, argument of $.proxy)
      .append( "I am a " + this.type + ", " )
​
      // `two` maps to `they`, the 2nd additional
      // argument in the $.proxy function call
      .append( "and they are " + two.type + ".<br>" )
​
      // The event type is "click"
      .append( "Thanks for " + event.type + "ing." )
​
      // The clicked element is `event.target`,
      // and its type is "button"
      .append( "the " + event.target.type + "." );
  }
};
​
var you = { type: "cat" };
var they = { type: "fish" };
​
// Set up handler to execute me.test() in the context
// of `me`, with `you` and `they` as additional arguments
var proxy = $.proxy( me.test, me, you, they );
​
$( "#test" )
  .on( "click", proxy );
</script>
​
</body>
</html>
```
     */
    proxy<TContext,
        TReturn>(funсtion: (this: TContext) => TReturn,
                 context: TContext): () => TReturn;

    // #endregion

    // region 1 parameters
    // #region 1 parameters

    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @param b An argument to be passed to the function referenced in the `function` argument.
     * @param c An argument to be passed to the function referenced in the `function` argument.
     * @param d An argument to be passed to the function referenced in the `function` argument.
     * @param e An argument to be passed to the function referenced in the `function` argument.
     * @param f An argument to be passed to the function referenced in the `function` argument.
     * @param g An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.4
     * @since 1.6
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     * @example ​ ````Change the context of functions bound to a click handler using the &quot;function, context&quot; signature. Unbind the first handler after first click.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  type: "zombie",
  test: function( event ) {
    // Without proxy, `this` would refer to the event target
    // use event.target to reference that element.
    var element = event.target;
    $( element ).css( "background-color", "red" );
​
    // With proxy, `this` refers to the me object encapsulating
    // this function.
    $( "#log" ).append( "Hello " + this.type + "<br>" );
    $( "#test" ).off( "click", this.test );
  }
};
​
var you = {
  type: "person",
  test: function( event ) {
    $( "#log" ).append( this.type + " " );
  }
};
​
// Execute you.test() in the context of the `you` object
// no matter where it is called
// i.e. the `this` keyword will refer to `you`
var youClick = $.proxy( you.test, you );
​
// attach click handlers to #test
$( "#test" )
  // this === "zombie"; handler unbound after first click
  .on( "click", $.proxy( me.test, me ) )
​
  // this === "person"
  .on( "click", youClick )
​
  // this === "zombie"
  .on( "click", $.proxy( you.test, me ) )
​
  // this === "<button> element"
  .on( "click", you.test );
</script>
​
</body>
</html>
```
     * @example ​ ````Change the context of a function bound to the click handler,
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  // I'm a dog
  type: "dog",
​
  // Note that event comes *after* one and two
  test: function( one, two, event ) {
    $( "#log" )
​
      // `one` maps to `you`, the 1st additional
      // argument in the $.proxy function call
      .append( "<h3>Hello " + one.type + ":</h3>" )
​
      // The `this` keyword refers to `me`
      // (the 2nd, context, argument of $.proxy)
      .append( "I am a " + this.type + ", " )
​
      // `two` maps to `they`, the 2nd additional
      // argument in the $.proxy function call
      .append( "and they are " + two.type + ".<br>" )
​
      // The event type is "click"
      .append( "Thanks for " + event.type + "ing." )
​
      // The clicked element is `event.target`,
      // and its type is "button"
      .append( "the " + event.target.type + "." );
  }
};
​
var you = { type: "cat" };
var they = { type: "fish" };
​
// Set up handler to execute me.test() in the context
// of `me`, with `you` and `they` as additional arguments
var proxy = $.proxy( me.test, me, you, they );
​
$( "#test" )
  .on( "click", proxy );
</script>
​
</body>
</html>
```
     */
    proxy<TContext,
        TReturn,
        A, B, C, D, E, F, G,
        T>(funсtion: (this: TContext, a: A, b: B, c: C, d: D, e: E, f: F, g: G,
                      t: T) => TReturn,
           context: TContext,
           a: A, b: B, c: C, d: D, e: E, f: F, g: G): (t: T) => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @param b An argument to be passed to the function referenced in the `function` argument.
     * @param c An argument to be passed to the function referenced in the `function` argument.
     * @param d An argument to be passed to the function referenced in the `function` argument.
     * @param e An argument to be passed to the function referenced in the `function` argument.
     * @param f An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.4
     * @since 1.6
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     * @example ​ ````Change the context of functions bound to a click handler using the &quot;function, context&quot; signature. Unbind the first handler after first click.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  type: "zombie",
  test: function( event ) {
    // Without proxy, `this` would refer to the event target
    // use event.target to reference that element.
    var element = event.target;
    $( element ).css( "background-color", "red" );
​
    // With proxy, `this` refers to the me object encapsulating
    // this function.
    $( "#log" ).append( "Hello " + this.type + "<br>" );
    $( "#test" ).off( "click", this.test );
  }
};
​
var you = {
  type: "person",
  test: function( event ) {
    $( "#log" ).append( this.type + " " );
  }
};
​
// Execute you.test() in the context of the `you` object
// no matter where it is called
// i.e. the `this` keyword will refer to `you`
var youClick = $.proxy( you.test, you );
​
// attach click handlers to #test
$( "#test" )
  // this === "zombie"; handler unbound after first click
  .on( "click", $.proxy( me.test, me ) )
​
  // this === "person"
  .on( "click", youClick )
​
  // this === "zombie"
  .on( "click", $.proxy( you.test, me ) )
​
  // this === "<button> element"
  .on( "click", you.test );
</script>
​
</body>
</html>
```
     * @example ​ ````Change the context of a function bound to the click handler,
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  // I'm a dog
  type: "dog",
​
  // Note that event comes *after* one and two
  test: function( one, two, event ) {
    $( "#log" )
​
      // `one` maps to `you`, the 1st additional
      // argument in the $.proxy function call
      .append( "<h3>Hello " + one.type + ":</h3>" )
​
      // The `this` keyword refers to `me`
      // (the 2nd, context, argument of $.proxy)
      .append( "I am a " + this.type + ", " )
​
      // `two` maps to `they`, the 2nd additional
      // argument in the $.proxy function call
      .append( "and they are " + two.type + ".<br>" )
​
      // The event type is "click"
      .append( "Thanks for " + event.type + "ing." )
​
      // The clicked element is `event.target`,
      // and its type is "button"
      .append( "the " + event.target.type + "." );
  }
};
​
var you = { type: "cat" };
var they = { type: "fish" };
​
// Set up handler to execute me.test() in the context
// of `me`, with `you` and `they` as additional arguments
var proxy = $.proxy( me.test, me, you, they );
​
$( "#test" )
  .on( "click", proxy );
</script>
​
</body>
</html>
```
     */
    proxy<TContext,
        TReturn,
        A, B, C, D, E, F,
        T>(funсtion: (this: TContext, a: A, b: B, c: C, d: D, e: E, f: F,
                      t: T) => TReturn,
           context: TContext,
           a: A, b: B, c: C, d: D, e: E, f: F): (t: T) => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @param b An argument to be passed to the function referenced in the `function` argument.
     * @param c An argument to be passed to the function referenced in the `function` argument.
     * @param d An argument to be passed to the function referenced in the `function` argument.
     * @param e An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.4
     * @since 1.6
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     * @example ​ ````Change the context of functions bound to a click handler using the &quot;function, context&quot; signature. Unbind the first handler after first click.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  type: "zombie",
  test: function( event ) {
    // Without proxy, `this` would refer to the event target
    // use event.target to reference that element.
    var element = event.target;
    $( element ).css( "background-color", "red" );
​
    // With proxy, `this` refers to the me object encapsulating
    // this function.
    $( "#log" ).append( "Hello " + this.type + "<br>" );
    $( "#test" ).off( "click", this.test );
  }
};
​
var you = {
  type: "person",
  test: function( event ) {
    $( "#log" ).append( this.type + " " );
  }
};
​
// Execute you.test() in the context of the `you` object
// no matter where it is called
// i.e. the `this` keyword will refer to `you`
var youClick = $.proxy( you.test, you );
​
// attach click handlers to #test
$( "#test" )
  // this === "zombie"; handler unbound after first click
  .on( "click", $.proxy( me.test, me ) )
​
  // this === "person"
  .on( "click", youClick )
​
  // this === "zombie"
  .on( "click", $.proxy( you.test, me ) )
​
  // this === "<button> element"
  .on( "click", you.test );
</script>
​
</body>
</html>
```
     * @example ​ ````Change the context of a function bound to the click handler,
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  // I'm a dog
  type: "dog",
​
  // Note that event comes *after* one and two
  test: function( one, two, event ) {
    $( "#log" )
​
      // `one` maps to `you`, the 1st additional
      // argument in the $.proxy function call
      .append( "<h3>Hello " + one.type + ":</h3>" )
​
      // The `this` keyword refers to `me`
      // (the 2nd, context, argument of $.proxy)
      .append( "I am a " + this.type + ", " )
​
      // `two` maps to `they`, the 2nd additional
      // argument in the $.proxy function call
      .append( "and they are " + two.type + ".<br>" )
​
      // The event type is "click"
      .append( "Thanks for " + event.type + "ing." )
​
      // The clicked element is `event.target`,
      // and its type is "button"
      .append( "the " + event.target.type + "." );
  }
};
​
var you = { type: "cat" };
var they = { type: "fish" };
​
// Set up handler to execute me.test() in the context
// of `me`, with `you` and `they` as additional arguments
var proxy = $.proxy( me.test, me, you, they );
​
$( "#test" )
  .on( "click", proxy );
</script>
​
</body>
</html>
```
     */
    proxy<TContext,
        TReturn,
        A, B, C, D, E,
        T>(funсtion: (this: TContext, a: A, b: B, c: C, d: D, e: E,
                      t: T) => TReturn,
           context: TContext,
           a: A, b: B, c: C, d: D, e: E): (t: T) => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @param b An argument to be passed to the function referenced in the `function` argument.
     * @param c An argument to be passed to the function referenced in the `function` argument.
     * @param d An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.4
     * @since 1.6
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     * @example ​ ````Change the context of functions bound to a click handler using the &quot;function, context&quot; signature. Unbind the first handler after first click.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  type: "zombie",
  test: function( event ) {
    // Without proxy, `this` would refer to the event target
    // use event.target to reference that element.
    var element = event.target;
    $( element ).css( "background-color", "red" );
​
    // With proxy, `this` refers to the me object encapsulating
    // this function.
    $( "#log" ).append( "Hello " + this.type + "<br>" );
    $( "#test" ).off( "click", this.test );
  }
};
​
var you = {
  type: "person",
  test: function( event ) {
    $( "#log" ).append( this.type + " " );
  }
};
​
// Execute you.test() in the context of the `you` object
// no matter where it is called
// i.e. the `this` keyword will refer to `you`
var youClick = $.proxy( you.test, you );
​
// attach click handlers to #test
$( "#test" )
  // this === "zombie"; handler unbound after first click
  .on( "click", $.proxy( me.test, me ) )
​
  // this === "person"
  .on( "click", youClick )
​
  // this === "zombie"
  .on( "click", $.proxy( you.test, me ) )
​
  // this === "<button> element"
  .on( "click", you.test );
</script>
​
</body>
</html>
```
     * @example ​ ````Change the context of a function bound to the click handler,
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  // I'm a dog
  type: "dog",
​
  // Note that event comes *after* one and two
  test: function( one, two, event ) {
    $( "#log" )
​
      // `one` maps to `you`, the 1st additional
      // argument in the $.proxy function call
      .append( "<h3>Hello " + one.type + ":</h3>" )
​
      // The `this` keyword refers to `me`
      // (the 2nd, context, argument of $.proxy)
      .append( "I am a " + this.type + ", " )
​
      // `two` maps to `they`, the 2nd additional
      // argument in the $.proxy function call
      .append( "and they are " + two.type + ".<br>" )
​
      // The event type is "click"
      .append( "Thanks for " + event.type + "ing." )
​
      // The clicked element is `event.target`,
      // and its type is "button"
      .append( "the " + event.target.type + "." );
  }
};
​
var you = { type: "cat" };
var they = { type: "fish" };
​
// Set up handler to execute me.test() in the context
// of `me`, with `you` and `they` as additional arguments
var proxy = $.proxy( me.test, me, you, they );
​
$( "#test" )
  .on( "click", proxy );
</script>
​
</body>
</html>
```
     */
    proxy<TContext,
        TReturn,
        A, B, C, D,
        T>(funсtion: (this: TContext, a: A, b: B, c: C, d: D,
                      t: T) => TReturn,
           context: TContext,
           a: A, b: B, c: C, d: D): (t: T) => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @param b An argument to be passed to the function referenced in the `function` argument.
     * @param c An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.4
     * @since 1.6
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     * @example ​ ````Change the context of functions bound to a click handler using the &quot;function, context&quot; signature. Unbind the first handler after first click.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  type: "zombie",
  test: function( event ) {
    // Without proxy, `this` would refer to the event target
    // use event.target to reference that element.
    var element = event.target;
    $( element ).css( "background-color", "red" );
​
    // With proxy, `this` refers to the me object encapsulating
    // this function.
    $( "#log" ).append( "Hello " + this.type + "<br>" );
    $( "#test" ).off( "click", this.test );
  }
};
​
var you = {
  type: "person",
  test: function( event ) {
    $( "#log" ).append( this.type + " " );
  }
};
​
// Execute you.test() in the context of the `you` object
// no matter where it is called
// i.e. the `this` keyword will refer to `you`
var youClick = $.proxy( you.test, you );
​
// attach click handlers to #test
$( "#test" )
  // this === "zombie"; handler unbound after first click
  .on( "click", $.proxy( me.test, me ) )
​
  // this === "person"
  .on( "click", youClick )
​
  // this === "zombie"
  .on( "click", $.proxy( you.test, me ) )
​
  // this === "<button> element"
  .on( "click", you.test );
</script>
​
</body>
</html>
```
     * @example ​ ````Change the context of a function bound to the click handler,
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  // I'm a dog
  type: "dog",
​
  // Note that event comes *after* one and two
  test: function( one, two, event ) {
    $( "#log" )
​
      // `one` maps to `you`, the 1st additional
      // argument in the $.proxy function call
      .append( "<h3>Hello " + one.type + ":</h3>" )
​
      // The `this` keyword refers to `me`
      // (the 2nd, context, argument of $.proxy)
      .append( "I am a " + this.type + ", " )
​
      // `two` maps to `they`, the 2nd additional
      // argument in the $.proxy function call
      .append( "and they are " + two.type + ".<br>" )
​
      // The event type is "click"
      .append( "Thanks for " + event.type + "ing." )
​
      // The clicked element is `event.target`,
      // and its type is "button"
      .append( "the " + event.target.type + "." );
  }
};
​
var you = { type: "cat" };
var they = { type: "fish" };
​
// Set up handler to execute me.test() in the context
// of `me`, with `you` and `they` as additional arguments
var proxy = $.proxy( me.test, me, you, they );
​
$( "#test" )
  .on( "click", proxy );
</script>
​
</body>
</html>
```
     */
    proxy<TContext,
        TReturn,
        A, B, C,
        T>(funсtion: (this: TContext, a: A, b: B, c: C,
                      t: T) => TReturn,
           context: TContext,
           a: A, b: B, c: C): (t: T) => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @param b An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.4
     * @since 1.6
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     * @example ​ ````Change the context of functions bound to a click handler using the &quot;function, context&quot; signature. Unbind the first handler after first click.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  type: "zombie",
  test: function( event ) {
    // Without proxy, `this` would refer to the event target
    // use event.target to reference that element.
    var element = event.target;
    $( element ).css( "background-color", "red" );
​
    // With proxy, `this` refers to the me object encapsulating
    // this function.
    $( "#log" ).append( "Hello " + this.type + "<br>" );
    $( "#test" ).off( "click", this.test );
  }
};
​
var you = {
  type: "person",
  test: function( event ) {
    $( "#log" ).append( this.type + " " );
  }
};
​
// Execute you.test() in the context of the `you` object
// no matter where it is called
// i.e. the `this` keyword will refer to `you`
var youClick = $.proxy( you.test, you );
​
// attach click handlers to #test
$( "#test" )
  // this === "zombie"; handler unbound after first click
  .on( "click", $.proxy( me.test, me ) )
​
  // this === "person"
  .on( "click", youClick )
​
  // this === "zombie"
  .on( "click", $.proxy( you.test, me ) )
​
  // this === "<button> element"
  .on( "click", you.test );
</script>
​
</body>
</html>
```
     * @example ​ ````Change the context of a function bound to the click handler,
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  // I'm a dog
  type: "dog",
​
  // Note that event comes *after* one and two
  test: function( one, two, event ) {
    $( "#log" )
​
      // `one` maps to `you`, the 1st additional
      // argument in the $.proxy function call
      .append( "<h3>Hello " + one.type + ":</h3>" )
​
      // The `this` keyword refers to `me`
      // (the 2nd, context, argument of $.proxy)
      .append( "I am a " + this.type + ", " )
​
      // `two` maps to `they`, the 2nd additional
      // argument in the $.proxy function call
      .append( "and they are " + two.type + ".<br>" )
​
      // The event type is "click"
      .append( "Thanks for " + event.type + "ing." )
​
      // The clicked element is `event.target`,
      // and its type is "button"
      .append( "the " + event.target.type + "." );
  }
};
​
var you = { type: "cat" };
var they = { type: "fish" };
​
// Set up handler to execute me.test() in the context
// of `me`, with `you` and `they` as additional arguments
var proxy = $.proxy( me.test, me, you, they );
​
$( "#test" )
  .on( "click", proxy );
</script>
​
</body>
</html>
```
     */
    proxy<TContext,
        TReturn,
        A, B,
        T>(funсtion: (this: TContext, a: A, b: B,
                      t: T) => TReturn,
           context: TContext,
           a: A, b: B): (t: T) => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.4
     * @since 1.6
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     * @example ​ ````Change the context of functions bound to a click handler using the &quot;function, context&quot; signature. Unbind the first handler after first click.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  type: "zombie",
  test: function( event ) {
    // Without proxy, `this` would refer to the event target
    // use event.target to reference that element.
    var element = event.target;
    $( element ).css( "background-color", "red" );
​
    // With proxy, `this` refers to the me object encapsulating
    // this function.
    $( "#log" ).append( "Hello " + this.type + "<br>" );
    $( "#test" ).off( "click", this.test );
  }
};
​
var you = {
  type: "person",
  test: function( event ) {
    $( "#log" ).append( this.type + " " );
  }
};
​
// Execute you.test() in the context of the `you` object
// no matter where it is called
// i.e. the `this` keyword will refer to `you`
var youClick = $.proxy( you.test, you );
​
// attach click handlers to #test
$( "#test" )
  // this === "zombie"; handler unbound after first click
  .on( "click", $.proxy( me.test, me ) )
​
  // this === "person"
  .on( "click", youClick )
​
  // this === "zombie"
  .on( "click", $.proxy( you.test, me ) )
​
  // this === "<button> element"
  .on( "click", you.test );
</script>
​
</body>
</html>
```
     * @example ​ ````Change the context of a function bound to the click handler,
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  // I'm a dog
  type: "dog",
​
  // Note that event comes *after* one and two
  test: function( one, two, event ) {
    $( "#log" )
​
      // `one` maps to `you`, the 1st additional
      // argument in the $.proxy function call
      .append( "<h3>Hello " + one.type + ":</h3>" )
​
      // The `this` keyword refers to `me`
      // (the 2nd, context, argument of $.proxy)
      .append( "I am a " + this.type + ", " )
​
      // `two` maps to `they`, the 2nd additional
      // argument in the $.proxy function call
      .append( "and they are " + two.type + ".<br>" )
​
      // The event type is "click"
      .append( "Thanks for " + event.type + "ing." )
​
      // The clicked element is `event.target`,
      // and its type is "button"
      .append( "the " + event.target.type + "." );
  }
};
​
var you = { type: "cat" };
var they = { type: "fish" };
​
// Set up handler to execute me.test() in the context
// of `me`, with `you` and `they` as additional arguments
var proxy = $.proxy( me.test, me, you, they );
​
$( "#test" )
  .on( "click", proxy );
</script>
​
</body>
</html>
```
     */
    proxy<TContext,
        TReturn,
        A,
        T>(funсtion: (this: TContext, a: A,
                      t: T) => TReturn,
           context: TContext,
           a: A): (t: T) => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.4
     * @since 1.6
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     * @example ​ ````Change the context of functions bound to a click handler using the &quot;function, context&quot; signature. Unbind the first handler after first click.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  type: "zombie",
  test: function( event ) {
    // Without proxy, `this` would refer to the event target
    // use event.target to reference that element.
    var element = event.target;
    $( element ).css( "background-color", "red" );
​
    // With proxy, `this` refers to the me object encapsulating
    // this function.
    $( "#log" ).append( "Hello " + this.type + "<br>" );
    $( "#test" ).off( "click", this.test );
  }
};
​
var you = {
  type: "person",
  test: function( event ) {
    $( "#log" ).append( this.type + " " );
  }
};
​
// Execute you.test() in the context of the `you` object
// no matter where it is called
// i.e. the `this` keyword will refer to `you`
var youClick = $.proxy( you.test, you );
​
// attach click handlers to #test
$( "#test" )
  // this === "zombie"; handler unbound after first click
  .on( "click", $.proxy( me.test, me ) )
​
  // this === "person"
  .on( "click", youClick )
​
  // this === "zombie"
  .on( "click", $.proxy( you.test, me ) )
​
  // this === "<button> element"
  .on( "click", you.test );
</script>
​
</body>
</html>
```
     * @example ​ ````Change the context of a function bound to the click handler,
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  // I'm a dog
  type: "dog",
​
  // Note that event comes *after* one and two
  test: function( one, two, event ) {
    $( "#log" )
​
      // `one` maps to `you`, the 1st additional
      // argument in the $.proxy function call
      .append( "<h3>Hello " + one.type + ":</h3>" )
​
      // The `this` keyword refers to `me`
      // (the 2nd, context, argument of $.proxy)
      .append( "I am a " + this.type + ", " )
​
      // `two` maps to `they`, the 2nd additional
      // argument in the $.proxy function call
      .append( "and they are " + two.type + ".<br>" )
​
      // The event type is "click"
      .append( "Thanks for " + event.type + "ing." )
​
      // The clicked element is `event.target`,
      // and its type is "button"
      .append( "the " + event.target.type + "." );
  }
};
​
var you = { type: "cat" };
var they = { type: "fish" };
​
// Set up handler to execute me.test() in the context
// of `me`, with `you` and `they` as additional arguments
var proxy = $.proxy( me.test, me, you, they );
​
$( "#test" )
  .on( "click", proxy );
</script>
​
</body>
</html>
```
     */
    proxy<TContext,
        TReturn,
        T>(funсtion: (this: TContext, t: T) => TReturn,
           context: TContext): (t: T) => TReturn;

    // #endregion

    // region 2 parameters
    // #region 2 parameters

    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @param b An argument to be passed to the function referenced in the `function` argument.
     * @param c An argument to be passed to the function referenced in the `function` argument.
     * @param d An argument to be passed to the function referenced in the `function` argument.
     * @param e An argument to be passed to the function referenced in the `function` argument.
     * @param f An argument to be passed to the function referenced in the `function` argument.
     * @param g An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.4
     * @since 1.6
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     * @example ​ ````Change the context of functions bound to a click handler using the &quot;function, context&quot; signature. Unbind the first handler after first click.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  type: "zombie",
  test: function( event ) {
    // Without proxy, `this` would refer to the event target
    // use event.target to reference that element.
    var element = event.target;
    $( element ).css( "background-color", "red" );
​
    // With proxy, `this` refers to the me object encapsulating
    // this function.
    $( "#log" ).append( "Hello " + this.type + "<br>" );
    $( "#test" ).off( "click", this.test );
  }
};
​
var you = {
  type: "person",
  test: function( event ) {
    $( "#log" ).append( this.type + " " );
  }
};
​
// Execute you.test() in the context of the `you` object
// no matter where it is called
// i.e. the `this` keyword will refer to `you`
var youClick = $.proxy( you.test, you );
​
// attach click handlers to #test
$( "#test" )
  // this === "zombie"; handler unbound after first click
  .on( "click", $.proxy( me.test, me ) )
​
  // this === "person"
  .on( "click", youClick )
​
  // this === "zombie"
  .on( "click", $.proxy( you.test, me ) )
​
  // this === "<button> element"
  .on( "click", you.test );
</script>
​
</body>
</html>
```
     * @example ​ ````Change the context of a function bound to the click handler,
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  // I'm a dog
  type: "dog",
​
  // Note that event comes *after* one and two
  test: function( one, two, event ) {
    $( "#log" )
​
      // `one` maps to `you`, the 1st additional
      // argument in the $.proxy function call
      .append( "<h3>Hello " + one.type + ":</h3>" )
​
      // The `this` keyword refers to `me`
      // (the 2nd, context, argument of $.proxy)
      .append( "I am a " + this.type + ", " )
​
      // `two` maps to `they`, the 2nd additional
      // argument in the $.proxy function call
      .append( "and they are " + two.type + ".<br>" )
​
      // The event type is "click"
      .append( "Thanks for " + event.type + "ing." )
​
      // The clicked element is `event.target`,
      // and its type is "button"
      .append( "the " + event.target.type + "." );
  }
};
​
var you = { type: "cat" };
var they = { type: "fish" };
​
// Set up handler to execute me.test() in the context
// of `me`, with `you` and `they` as additional arguments
var proxy = $.proxy( me.test, me, you, they );
​
$( "#test" )
  .on( "click", proxy );
</script>
​
</body>
</html>
```
     */
    proxy<TContext,
        TReturn,
        A, B, C, D, E, F, G,
        T, U>(funсtion: (this: TContext, a: A, b: B, c: C, d: D, e: E, f: F, g: G,
                         t: T, u: U) => TReturn,
              context: TContext,
              a: A, b: B, c: C, d: D, e: E, f: F, g: G): (t: T, u: U) => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @param b An argument to be passed to the function referenced in the `function` argument.
     * @param c An argument to be passed to the function referenced in the `function` argument.
     * @param d An argument to be passed to the function referenced in the `function` argument.
     * @param e An argument to be passed to the function referenced in the `function` argument.
     * @param f An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.4
     * @since 1.6
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     * @example ​ ````Change the context of functions bound to a click handler using the &quot;function, context&quot; signature. Unbind the first handler after first click.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  type: "zombie",
  test: function( event ) {
    // Without proxy, `this` would refer to the event target
    // use event.target to reference that element.
    var element = event.target;
    $( element ).css( "background-color", "red" );
​
    // With proxy, `this` refers to the me object encapsulating
    // this function.
    $( "#log" ).append( "Hello " + this.type + "<br>" );
    $( "#test" ).off( "click", this.test );
  }
};
​
var you = {
  type: "person",
  test: function( event ) {
    $( "#log" ).append( this.type + " " );
  }
};
​
// Execute you.test() in the context of the `you` object
// no matter where it is called
// i.e. the `this` keyword will refer to `you`
var youClick = $.proxy( you.test, you );
​
// attach click handlers to #test
$( "#test" )
  // this === "zombie"; handler unbound after first click
  .on( "click", $.proxy( me.test, me ) )
​
  // this === "person"
  .on( "click", youClick )
​
  // this === "zombie"
  .on( "click", $.proxy( you.test, me ) )
​
  // this === "<button> element"
  .on( "click", you.test );
</script>
​
</body>
</html>
```
     * @example ​ ````Change the context of a function bound to the click handler,
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  // I'm a dog
  type: "dog",
​
  // Note that event comes *after* one and two
  test: function( one, two, event ) {
    $( "#log" )
​
      // `one` maps to `you`, the 1st additional
      // argument in the $.proxy function call
      .append( "<h3>Hello " + one.type + ":</h3>" )
​
      // The `this` keyword refers to `me`
      // (the 2nd, context, argument of $.proxy)
      .append( "I am a " + this.type + ", " )
​
      // `two` maps to `they`, the 2nd additional
      // argument in the $.proxy function call
      .append( "and they are " + two.type + ".<br>" )
​
      // The event type is "click"
      .append( "Thanks for " + event.type + "ing." )
​
      // The clicked element is `event.target`,
      // and its type is "button"
      .append( "the " + event.target.type + "." );
  }
};
​
var you = { type: "cat" };
var they = { type: "fish" };
​
// Set up handler to execute me.test() in the context
// of `me`, with `you` and `they` as additional arguments
var proxy = $.proxy( me.test, me, you, they );
​
$( "#test" )
  .on( "click", proxy );
</script>
​
</body>
</html>
```
     */
    proxy<TContext,
        TReturn,
        A, B, C, D, E, F,
        T, U>(funсtion: (this: TContext, a: A, b: B, c: C, d: D, e: E, f: F,
                         t: T, u: U) => TReturn,
              context: TContext,
              a: A, b: B, c: C, d: D, e: E, f: F): (t: T, u: U) => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @param b An argument to be passed to the function referenced in the `function` argument.
     * @param c An argument to be passed to the function referenced in the `function` argument.
     * @param d An argument to be passed to the function referenced in the `function` argument.
     * @param e An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.4
     * @since 1.6
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     * @example ​ ````Change the context of functions bound to a click handler using the &quot;function, context&quot; signature. Unbind the first handler after first click.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  type: "zombie",
  test: function( event ) {
    // Without proxy, `this` would refer to the event target
    // use event.target to reference that element.
    var element = event.target;
    $( element ).css( "background-color", "red" );
​
    // With proxy, `this` refers to the me object encapsulating
    // this function.
    $( "#log" ).append( "Hello " + this.type + "<br>" );
    $( "#test" ).off( "click", this.test );
  }
};
​
var you = {
  type: "person",
  test: function( event ) {
    $( "#log" ).append( this.type + " " );
  }
};
​
// Execute you.test() in the context of the `you` object
// no matter where it is called
// i.e. the `this` keyword will refer to `you`
var youClick = $.proxy( you.test, you );
​
// attach click handlers to #test
$( "#test" )
  // this === "zombie"; handler unbound after first click
  .on( "click", $.proxy( me.test, me ) )
​
  // this === "person"
  .on( "click", youClick )
​
  // this === "zombie"
  .on( "click", $.proxy( you.test, me ) )
​
  // this === "<button> element"
  .on( "click", you.test );
</script>
​
</body>
</html>
```
     * @example ​ ````Change the context of a function bound to the click handler,
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  // I'm a dog
  type: "dog",
​
  // Note that event comes *after* one and two
  test: function( one, two, event ) {
    $( "#log" )
​
      // `one` maps to `you`, the 1st additional
      // argument in the $.proxy function call
      .append( "<h3>Hello " + one.type + ":</h3>" )
​
      // The `this` keyword refers to `me`
      // (the 2nd, context, argument of $.proxy)
      .append( "I am a " + this.type + ", " )
​
      // `two` maps to `they`, the 2nd additional
      // argument in the $.proxy function call
      .append( "and they are " + two.type + ".<br>" )
​
      // The event type is "click"
      .append( "Thanks for " + event.type + "ing." )
​
      // The clicked element is `event.target`,
      // and its type is "button"
      .append( "the " + event.target.type + "." );
  }
};
​
var you = { type: "cat" };
var they = { type: "fish" };
​
// Set up handler to execute me.test() in the context
// of `me`, with `you` and `they` as additional arguments
var proxy = $.proxy( me.test, me, you, they );
​
$( "#test" )
  .on( "click", proxy );
</script>
​
</body>
</html>
```
     */
    proxy<TContext,
        TReturn,
        A, B, C, D, E,
        T, U>(funсtion: (this: TContext, a: A, b: B, c: C, d: D, e: E,
                         t: T, u: U) => TReturn,
              context: TContext,
              a: A, b: B, c: C, d: D, e: E): (t: T, u: U) => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @param b An argument to be passed to the function referenced in the `function` argument.
     * @param c An argument to be passed to the function referenced in the `function` argument.
     * @param d An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.4
     * @since 1.6
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     * @example ​ ````Change the context of functions bound to a click handler using the &quot;function, context&quot; signature. Unbind the first handler after first click.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  type: "zombie",
  test: function( event ) {
    // Without proxy, `this` would refer to the event target
    // use event.target to reference that element.
    var element = event.target;
    $( element ).css( "background-color", "red" );
​
    // With proxy, `this` refers to the me object encapsulating
    // this function.
    $( "#log" ).append( "Hello " + this.type + "<br>" );
    $( "#test" ).off( "click", this.test );
  }
};
​
var you = {
  type: "person",
  test: function( event ) {
    $( "#log" ).append( this.type + " " );
  }
};
​
// Execute you.test() in the context of the `you` object
// no matter where it is called
// i.e. the `this` keyword will refer to `you`
var youClick = $.proxy( you.test, you );
​
// attach click handlers to #test
$( "#test" )
  // this === "zombie"; handler unbound after first click
  .on( "click", $.proxy( me.test, me ) )
​
  // this === "person"
  .on( "click", youClick )
​
  // this === "zombie"
  .on( "click", $.proxy( you.test, me ) )
​
  // this === "<button> element"
  .on( "click", you.test );
</script>
​
</body>
</html>
```
     * @example ​ ````Change the context of a function bound to the click handler,
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  // I'm a dog
  type: "dog",
​
  // Note that event comes *after* one and two
  test: function( one, two, event ) {
    $( "#log" )
​
      // `one` maps to `you`, the 1st additional
      // argument in the $.proxy function call
      .append( "<h3>Hello " + one.type + ":</h3>" )
​
      // The `this` keyword refers to `me`
      // (the 2nd, context, argument of $.proxy)
      .append( "I am a " + this.type + ", " )
​
      // `two` maps to `they`, the 2nd additional
      // argument in the $.proxy function call
      .append( "and they are " + two.type + ".<br>" )
​
      // The event type is "click"
      .append( "Thanks for " + event.type + "ing." )
​
      // The clicked element is `event.target`,
      // and its type is "button"
      .append( "the " + event.target.type + "." );
  }
};
​
var you = { type: "cat" };
var they = { type: "fish" };
​
// Set up handler to execute me.test() in the context
// of `me`, with `you` and `they` as additional arguments
var proxy = $.proxy( me.test, me, you, they );
​
$( "#test" )
  .on( "click", proxy );
</script>
​
</body>
</html>
```
     */
    proxy<TContext,
        TReturn,
        A, B, C, D,
        T, U>(funсtion: (this: TContext, a: A, b: B, c: C, d: D,
                         t: T, u: U) => TReturn,
              context: TContext,
              a: A, b: B, c: C, d: D): (t: T, u: U) => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @param b An argument to be passed to the function referenced in the `function` argument.
     * @param c An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.4
     * @since 1.6
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     * @example ​ ````Change the context of functions bound to a click handler using the &quot;function, context&quot; signature. Unbind the first handler after first click.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  type: "zombie",
  test: function( event ) {
    // Without proxy, `this` would refer to the event target
    // use event.target to reference that element.
    var element = event.target;
    $( element ).css( "background-color", "red" );
​
    // With proxy, `this` refers to the me object encapsulating
    // this function.
    $( "#log" ).append( "Hello " + this.type + "<br>" );
    $( "#test" ).off( "click", this.test );
  }
};
​
var you = {
  type: "person",
  test: function( event ) {
    $( "#log" ).append( this.type + " " );
  }
};
​
// Execute you.test() in the context of the `you` object
// no matter where it is called
// i.e. the `this` keyword will refer to `you`
var youClick = $.proxy( you.test, you );
​
// attach click handlers to #test
$( "#test" )
  // this === "zombie"; handler unbound after first click
  .on( "click", $.proxy( me.test, me ) )
​
  // this === "person"
  .on( "click", youClick )
​
  // this === "zombie"
  .on( "click", $.proxy( you.test, me ) )
​
  // this === "<button> element"
  .on( "click", you.test );
</script>
​
</body>
</html>
```
     * @example ​ ````Change the context of a function bound to the click handler,
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  // I'm a dog
  type: "dog",
​
  // Note that event comes *after* one and two
  test: function( one, two, event ) {
    $( "#log" )
​
      // `one` maps to `you`, the 1st additional
      // argument in the $.proxy function call
      .append( "<h3>Hello " + one.type + ":</h3>" )
​
      // The `this` keyword refers to `me`
      // (the 2nd, context, argument of $.proxy)
      .append( "I am a " + this.type + ", " )
​
      // `two` maps to `they`, the 2nd additional
      // argument in the $.proxy function call
      .append( "and they are " + two.type + ".<br>" )
​
      // The event type is "click"
      .append( "Thanks for " + event.type + "ing." )
​
      // The clicked element is `event.target`,
      // and its type is "button"
      .append( "the " + event.target.type + "." );
  }
};
​
var you = { type: "cat" };
var they = { type: "fish" };
​
// Set up handler to execute me.test() in the context
// of `me`, with `you` and `they` as additional arguments
var proxy = $.proxy( me.test, me, you, they );
​
$( "#test" )
  .on( "click", proxy );
</script>
​
</body>
</html>
```
     */
    proxy<TContext,
        TReturn,
        A, B, C,
        T, U>(funсtion: (this: TContext, a: A, b: B, c: C,
                         t: T, u: U) => TReturn,
              context: TContext,
              a: A, b: B, c: C): (t: T, u: U) => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @param b An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.4
     * @since 1.6
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     * @example ​ ````Change the context of functions bound to a click handler using the &quot;function, context&quot; signature. Unbind the first handler after first click.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  type: "zombie",
  test: function( event ) {
    // Without proxy, `this` would refer to the event target
    // use event.target to reference that element.
    var element = event.target;
    $( element ).css( "background-color", "red" );
​
    // With proxy, `this` refers to the me object encapsulating
    // this function.
    $( "#log" ).append( "Hello " + this.type + "<br>" );
    $( "#test" ).off( "click", this.test );
  }
};
​
var you = {
  type: "person",
  test: function( event ) {
    $( "#log" ).append( this.type + " " );
  }
};
​
// Execute you.test() in the context of the `you` object
// no matter where it is called
// i.e. the `this` keyword will refer to `you`
var youClick = $.proxy( you.test, you );
​
// attach click handlers to #test
$( "#test" )
  // this === "zombie"; handler unbound after first click
  .on( "click", $.proxy( me.test, me ) )
​
  // this === "person"
  .on( "click", youClick )
​
  // this === "zombie"
  .on( "click", $.proxy( you.test, me ) )
​
  // this === "<button> element"
  .on( "click", you.test );
</script>
​
</body>
</html>
```
     * @example ​ ````Change the context of a function bound to the click handler,
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  // I'm a dog
  type: "dog",
​
  // Note that event comes *after* one and two
  test: function( one, two, event ) {
    $( "#log" )
​
      // `one` maps to `you`, the 1st additional
      // argument in the $.proxy function call
      .append( "<h3>Hello " + one.type + ":</h3>" )
​
      // The `this` keyword refers to `me`
      // (the 2nd, context, argument of $.proxy)
      .append( "I am a " + this.type + ", " )
​
      // `two` maps to `they`, the 2nd additional
      // argument in the $.proxy function call
      .append( "and they are " + two.type + ".<br>" )
​
      // The event type is "click"
      .append( "Thanks for " + event.type + "ing." )
​
      // The clicked element is `event.target`,
      // and its type is "button"
      .append( "the " + event.target.type + "." );
  }
};
​
var you = { type: "cat" };
var they = { type: "fish" };
​
// Set up handler to execute me.test() in the context
// of `me`, with `you` and `they` as additional arguments
var proxy = $.proxy( me.test, me, you, they );
​
$( "#test" )
  .on( "click", proxy );
</script>
​
</body>
</html>
```
     */
    proxy<TContext,
        TReturn,
        A, B,
        T, U>(funсtion: (this: TContext, a: A, b: B,
                         t: T, u: U) => TReturn,
              context: TContext,
              a: A, b: B): (t: T, u: U) => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.4
     * @since 1.6
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     * @example ​ ````Change the context of functions bound to a click handler using the &quot;function, context&quot; signature. Unbind the first handler after first click.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  type: "zombie",
  test: function( event ) {
    // Without proxy, `this` would refer to the event target
    // use event.target to reference that element.
    var element = event.target;
    $( element ).css( "background-color", "red" );
​
    // With proxy, `this` refers to the me object encapsulating
    // this function.
    $( "#log" ).append( "Hello " + this.type + "<br>" );
    $( "#test" ).off( "click", this.test );
  }
};
​
var you = {
  type: "person",
  test: function( event ) {
    $( "#log" ).append( this.type + " " );
  }
};
​
// Execute you.test() in the context of the `you` object
// no matter where it is called
// i.e. the `this` keyword will refer to `you`
var youClick = $.proxy( you.test, you );
​
// attach click handlers to #test
$( "#test" )
  // this === "zombie"; handler unbound after first click
  .on( "click", $.proxy( me.test, me ) )
​
  // this === "person"
  .on( "click", youClick )
​
  // this === "zombie"
  .on( "click", $.proxy( you.test, me ) )
​
  // this === "<button> element"
  .on( "click", you.test );
</script>
​
</body>
</html>
```
     * @example ​ ````Change the context of a function bound to the click handler,
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  // I'm a dog
  type: "dog",
​
  // Note that event comes *after* one and two
  test: function( one, two, event ) {
    $( "#log" )
​
      // `one` maps to `you`, the 1st additional
      // argument in the $.proxy function call
      .append( "<h3>Hello " + one.type + ":</h3>" )
​
      // The `this` keyword refers to `me`
      // (the 2nd, context, argument of $.proxy)
      .append( "I am a " + this.type + ", " )
​
      // `two` maps to `they`, the 2nd additional
      // argument in the $.proxy function call
      .append( "and they are " + two.type + ".<br>" )
​
      // The event type is "click"
      .append( "Thanks for " + event.type + "ing." )
​
      // The clicked element is `event.target`,
      // and its type is "button"
      .append( "the " + event.target.type + "." );
  }
};
​
var you = { type: "cat" };
var they = { type: "fish" };
​
// Set up handler to execute me.test() in the context
// of `me`, with `you` and `they` as additional arguments
var proxy = $.proxy( me.test, me, you, they );
​
$( "#test" )
  .on( "click", proxy );
</script>
​
</body>
</html>
```
     */
    proxy<TContext,
        TReturn,
        A,
        T, U>(funсtion: (this: TContext, a: A,
                         t: T, u: U) => TReturn,
              context: TContext,
              a: A): (t: T, u: U) => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.4
     * @since 1.6
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     * @example ​ ````Change the context of functions bound to a click handler using the &quot;function, context&quot; signature. Unbind the first handler after first click.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  type: "zombie",
  test: function( event ) {
    // Without proxy, `this` would refer to the event target
    // use event.target to reference that element.
    var element = event.target;
    $( element ).css( "background-color", "red" );
​
    // With proxy, `this` refers to the me object encapsulating
    // this function.
    $( "#log" ).append( "Hello " + this.type + "<br>" );
    $( "#test" ).off( "click", this.test );
  }
};
​
var you = {
  type: "person",
  test: function( event ) {
    $( "#log" ).append( this.type + " " );
  }
};
​
// Execute you.test() in the context of the `you` object
// no matter where it is called
// i.e. the `this` keyword will refer to `you`
var youClick = $.proxy( you.test, you );
​
// attach click handlers to #test
$( "#test" )
  // this === "zombie"; handler unbound after first click
  .on( "click", $.proxy( me.test, me ) )
​
  // this === "person"
  .on( "click", youClick )
​
  // this === "zombie"
  .on( "click", $.proxy( you.test, me ) )
​
  // this === "<button> element"
  .on( "click", you.test );
</script>
​
</body>
</html>
```
     * @example ​ ````Change the context of a function bound to the click handler,
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  // I'm a dog
  type: "dog",
​
  // Note that event comes *after* one and two
  test: function( one, two, event ) {
    $( "#log" )
​
      // `one` maps to `you`, the 1st additional
      // argument in the $.proxy function call
      .append( "<h3>Hello " + one.type + ":</h3>" )
​
      // The `this` keyword refers to `me`
      // (the 2nd, context, argument of $.proxy)
      .append( "I am a " + this.type + ", " )
​
      // `two` maps to `they`, the 2nd additional
      // argument in the $.proxy function call
      .append( "and they are " + two.type + ".<br>" )
​
      // The event type is "click"
      .append( "Thanks for " + event.type + "ing." )
​
      // The clicked element is `event.target`,
      // and its type is "button"
      .append( "the " + event.target.type + "." );
  }
};
​
var you = { type: "cat" };
var they = { type: "fish" };
​
// Set up handler to execute me.test() in the context
// of `me`, with `you` and `they` as additional arguments
var proxy = $.proxy( me.test, me, you, they );
​
$( "#test" )
  .on( "click", proxy );
</script>
​
</body>
</html>
```
     */
    proxy<TContext,
        TReturn,
        T, U>(funсtion: (this: TContext, t: T, u: U) => TReturn,
              context: TContext): (t: T, u: U) => TReturn;

    // #endregion

    // region 3 parameters
    // #region 3 parameters

    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @param b An argument to be passed to the function referenced in the `function` argument.
     * @param c An argument to be passed to the function referenced in the `function` argument.
     * @param d An argument to be passed to the function referenced in the `function` argument.
     * @param e An argument to be passed to the function referenced in the `function` argument.
     * @param f An argument to be passed to the function referenced in the `function` argument.
     * @param g An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.4
     * @since 1.6
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     * @example ​ ````Change the context of functions bound to a click handler using the &quot;function, context&quot; signature. Unbind the first handler after first click.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  type: "zombie",
  test: function( event ) {
    // Without proxy, `this` would refer to the event target
    // use event.target to reference that element.
    var element = event.target;
    $( element ).css( "background-color", "red" );
​
    // With proxy, `this` refers to the me object encapsulating
    // this function.
    $( "#log" ).append( "Hello " + this.type + "<br>" );
    $( "#test" ).off( "click", this.test );
  }
};
​
var you = {
  type: "person",
  test: function( event ) {
    $( "#log" ).append( this.type + " " );
  }
};
​
// Execute you.test() in the context of the `you` object
// no matter where it is called
// i.e. the `this` keyword will refer to `you`
var youClick = $.proxy( you.test, you );
​
// attach click handlers to #test
$( "#test" )
  // this === "zombie"; handler unbound after first click
  .on( "click", $.proxy( me.test, me ) )
​
  // this === "person"
  .on( "click", youClick )
​
  // this === "zombie"
  .on( "click", $.proxy( you.test, me ) )
​
  // this === "<button> element"
  .on( "click", you.test );
</script>
​
</body>
</html>
```
     * @example ​ ````Change the context of a function bound to the click handler,
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  // I'm a dog
  type: "dog",
​
  // Note that event comes *after* one and two
  test: function( one, two, event ) {
    $( "#log" )
​
      // `one` maps to `you`, the 1st additional
      // argument in the $.proxy function call
      .append( "<h3>Hello " + one.type + ":</h3>" )
​
      // The `this` keyword refers to `me`
      // (the 2nd, context, argument of $.proxy)
      .append( "I am a " + this.type + ", " )
​
      // `two` maps to `they`, the 2nd additional
      // argument in the $.proxy function call
      .append( "and they are " + two.type + ".<br>" )
​
      // The event type is "click"
      .append( "Thanks for " + event.type + "ing." )
​
      // The clicked element is `event.target`,
      // and its type is "button"
      .append( "the " + event.target.type + "." );
  }
};
​
var you = { type: "cat" };
var they = { type: "fish" };
​
// Set up handler to execute me.test() in the context
// of `me`, with `you` and `they` as additional arguments
var proxy = $.proxy( me.test, me, you, they );
​
$( "#test" )
  .on( "click", proxy );
</script>
​
</body>
</html>
```
     */
    proxy<TContext,
        TReturn,
        A, B, C, D, E, F, G,
        T, U, V>(funсtion: (this: TContext, a: A, b: B, c: C, d: D, e: E, f: F, g: G,
                            t: T, u: U, v: V) => TReturn,
                 context: TContext,
                 a: A, b: B, c: C, d: D, e: E, f: F, g: G): (t: T, u: U, v: V) => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @param b An argument to be passed to the function referenced in the `function` argument.
     * @param c An argument to be passed to the function referenced in the `function` argument.
     * @param d An argument to be passed to the function referenced in the `function` argument.
     * @param e An argument to be passed to the function referenced in the `function` argument.
     * @param f An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.4
     * @since 1.6
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     * @example ​ ````Change the context of functions bound to a click handler using the &quot;function, context&quot; signature. Unbind the first handler after first click.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  type: "zombie",
  test: function( event ) {
    // Without proxy, `this` would refer to the event target
    // use event.target to reference that element.
    var element = event.target;
    $( element ).css( "background-color", "red" );
​
    // With proxy, `this` refers to the me object encapsulating
    // this function.
    $( "#log" ).append( "Hello " + this.type + "<br>" );
    $( "#test" ).off( "click", this.test );
  }
};
​
var you = {
  type: "person",
  test: function( event ) {
    $( "#log" ).append( this.type + " " );
  }
};
​
// Execute you.test() in the context of the `you` object
// no matter where it is called
// i.e. the `this` keyword will refer to `you`
var youClick = $.proxy( you.test, you );
​
// attach click handlers to #test
$( "#test" )
  // this === "zombie"; handler unbound after first click
  .on( "click", $.proxy( me.test, me ) )
​
  // this === "person"
  .on( "click", youClick )
​
  // this === "zombie"
  .on( "click", $.proxy( you.test, me ) )
​
  // this === "<button> element"
  .on( "click", you.test );
</script>
​
</body>
</html>
```
     * @example ​ ````Change the context of a function bound to the click handler,
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  // I'm a dog
  type: "dog",
​
  // Note that event comes *after* one and two
  test: function( one, two, event ) {
    $( "#log" )
​
      // `one` maps to `you`, the 1st additional
      // argument in the $.proxy function call
      .append( "<h3>Hello " + one.type + ":</h3>" )
​
      // The `this` keyword refers to `me`
      // (the 2nd, context, argument of $.proxy)
      .append( "I am a " + this.type + ", " )
​
      // `two` maps to `they`, the 2nd additional
      // argument in the $.proxy function call
      .append( "and they are " + two.type + ".<br>" )
​
      // The event type is "click"
      .append( "Thanks for " + event.type + "ing." )
​
      // The clicked element is `event.target`,
      // and its type is "button"
      .append( "the " + event.target.type + "." );
  }
};
​
var you = { type: "cat" };
var they = { type: "fish" };
​
// Set up handler to execute me.test() in the context
// of `me`, with `you` and `they` as additional arguments
var proxy = $.proxy( me.test, me, you, they );
​
$( "#test" )
  .on( "click", proxy );
</script>
​
</body>
</html>
```
     */
    proxy<TContext,
        TReturn,
        A, B, C, D, E, F,
        T, U, V>(funсtion: (this: TContext, a: A, b: B, c: C, d: D, e: E, f: F,
                            t: T, u: U, v: V) => TReturn,
                 context: TContext,
                 a: A, b: B, c: C, d: D, e: E, f: F): (t: T, u: U, v: V) => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @param b An argument to be passed to the function referenced in the `function` argument.
     * @param c An argument to be passed to the function referenced in the `function` argument.
     * @param d An argument to be passed to the function referenced in the `function` argument.
     * @param e An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.4
     * @since 1.6
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     * @example ​ ````Change the context of functions bound to a click handler using the &quot;function, context&quot; signature. Unbind the first handler after first click.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  type: "zombie",
  test: function( event ) {
    // Without proxy, `this` would refer to the event target
    // use event.target to reference that element.
    var element = event.target;
    $( element ).css( "background-color", "red" );
​
    // With proxy, `this` refers to the me object encapsulating
    // this function.
    $( "#log" ).append( "Hello " + this.type + "<br>" );
    $( "#test" ).off( "click", this.test );
  }
};
​
var you = {
  type: "person",
  test: function( event ) {
    $( "#log" ).append( this.type + " " );
  }
};
​
// Execute you.test() in the context of the `you` object
// no matter where it is called
// i.e. the `this` keyword will refer to `you`
var youClick = $.proxy( you.test, you );
​
// attach click handlers to #test
$( "#test" )
  // this === "zombie"; handler unbound after first click
  .on( "click", $.proxy( me.test, me ) )
​
  // this === "person"
  .on( "click", youClick )
​
  // this === "zombie"
  .on( "click", $.proxy( you.test, me ) )
​
  // this === "<button> element"
  .on( "click", you.test );
</script>
​
</body>
</html>
```
     * @example ​ ````Change the context of a function bound to the click handler,
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  // I'm a dog
  type: "dog",
​
  // Note that event comes *after* one and two
  test: function( one, two, event ) {
    $( "#log" )
​
      // `one` maps to `you`, the 1st additional
      // argument in the $.proxy function call
      .append( "<h3>Hello " + one.type + ":</h3>" )
​
      // The `this` keyword refers to `me`
      // (the 2nd, context, argument of $.proxy)
      .append( "I am a " + this.type + ", " )
​
      // `two` maps to `they`, the 2nd additional
      // argument in the $.proxy function call
      .append( "and they are " + two.type + ".<br>" )
​
      // The event type is "click"
      .append( "Thanks for " + event.type + "ing." )
​
      // The clicked element is `event.target`,
      // and its type is "button"
      .append( "the " + event.target.type + "." );
  }
};
​
var you = { type: "cat" };
var they = { type: "fish" };
​
// Set up handler to execute me.test() in the context
// of `me`, with `you` and `they` as additional arguments
var proxy = $.proxy( me.test, me, you, they );
​
$( "#test" )
  .on( "click", proxy );
</script>
​
</body>
</html>
```
     */
    proxy<TContext,
        TReturn,
        A, B, C, D, E,
        T, U, V>(funсtion: (this: TContext, a: A, b: B, c: C, d: D, e: E,
                            t: T, u: U, v: V) => TReturn,
                 context: TContext,
                 a: A, b: B, c: C, d: D, e: E): (t: T, u: U, v: V) => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @param b An argument to be passed to the function referenced in the `function` argument.
     * @param c An argument to be passed to the function referenced in the `function` argument.
     * @param d An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.4
     * @since 1.6
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     * @example ​ ````Change the context of functions bound to a click handler using the &quot;function, context&quot; signature. Unbind the first handler after first click.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  type: "zombie",
  test: function( event ) {
    // Without proxy, `this` would refer to the event target
    // use event.target to reference that element.
    var element = event.target;
    $( element ).css( "background-color", "red" );
​
    // With proxy, `this` refers to the me object encapsulating
    // this function.
    $( "#log" ).append( "Hello " + this.type + "<br>" );
    $( "#test" ).off( "click", this.test );
  }
};
​
var you = {
  type: "person",
  test: function( event ) {
    $( "#log" ).append( this.type + " " );
  }
};
​
// Execute you.test() in the context of the `you` object
// no matter where it is called
// i.e. the `this` keyword will refer to `you`
var youClick = $.proxy( you.test, you );
​
// attach click handlers to #test
$( "#test" )
  // this === "zombie"; handler unbound after first click
  .on( "click", $.proxy( me.test, me ) )
​
  // this === "person"
  .on( "click", youClick )
​
  // this === "zombie"
  .on( "click", $.proxy( you.test, me ) )
​
  // this === "<button> element"
  .on( "click", you.test );
</script>
​
</body>
</html>
```
     * @example ​ ````Change the context of a function bound to the click handler,
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  // I'm a dog
  type: "dog",
​
  // Note that event comes *after* one and two
  test: function( one, two, event ) {
    $( "#log" )
​
      // `one` maps to `you`, the 1st additional
      // argument in the $.proxy function call
      .append( "<h3>Hello " + one.type + ":</h3>" )
​
      // The `this` keyword refers to `me`
      // (the 2nd, context, argument of $.proxy)
      .append( "I am a " + this.type + ", " )
​
      // `two` maps to `they`, the 2nd additional
      // argument in the $.proxy function call
      .append( "and they are " + two.type + ".<br>" )
​
      // The event type is "click"
      .append( "Thanks for " + event.type + "ing." )
​
      // The clicked element is `event.target`,
      // and its type is "button"
      .append( "the " + event.target.type + "." );
  }
};
​
var you = { type: "cat" };
var they = { type: "fish" };
​
// Set up handler to execute me.test() in the context
// of `me`, with `you` and `they` as additional arguments
var proxy = $.proxy( me.test, me, you, they );
​
$( "#test" )
  .on( "click", proxy );
</script>
​
</body>
</html>
```
     */
    proxy<TContext,
        TReturn,
        A, B, C, D,
        T, U, V>(funсtion: (this: TContext, a: A, b: B, c: C, d: D,
                            t: T, u: U, v: V) => TReturn,
                 context: TContext,
                 a: A, b: B, c: C, d: D): (t: T, u: U, v: V) => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @param b An argument to be passed to the function referenced in the `function` argument.
     * @param c An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.4
     * @since 1.6
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     * @example ​ ````Change the context of functions bound to a click handler using the &quot;function, context&quot; signature. Unbind the first handler after first click.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  type: "zombie",
  test: function( event ) {
    // Without proxy, `this` would refer to the event target
    // use event.target to reference that element.
    var element = event.target;
    $( element ).css( "background-color", "red" );
​
    // With proxy, `this` refers to the me object encapsulating
    // this function.
    $( "#log" ).append( "Hello " + this.type + "<br>" );
    $( "#test" ).off( "click", this.test );
  }
};
​
var you = {
  type: "person",
  test: function( event ) {
    $( "#log" ).append( this.type + " " );
  }
};
​
// Execute you.test() in the context of the `you` object
// no matter where it is called
// i.e. the `this` keyword will refer to `you`
var youClick = $.proxy( you.test, you );
​
// attach click handlers to #test
$( "#test" )
  // this === "zombie"; handler unbound after first click
  .on( "click", $.proxy( me.test, me ) )
​
  // this === "person"
  .on( "click", youClick )
​
  // this === "zombie"
  .on( "click", $.proxy( you.test, me ) )
​
  // this === "<button> element"
  .on( "click", you.test );
</script>
​
</body>
</html>
```
     * @example ​ ````Change the context of a function bound to the click handler,
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  // I'm a dog
  type: "dog",
​
  // Note that event comes *after* one and two
  test: function( one, two, event ) {
    $( "#log" )
​
      // `one` maps to `you`, the 1st additional
      // argument in the $.proxy function call
      .append( "<h3>Hello " + one.type + ":</h3>" )
​
      // The `this` keyword refers to `me`
      // (the 2nd, context, argument of $.proxy)
      .append( "I am a " + this.type + ", " )
​
      // `two` maps to `they`, the 2nd additional
      // argument in the $.proxy function call
      .append( "and they are " + two.type + ".<br>" )
​
      // The event type is "click"
      .append( "Thanks for " + event.type + "ing." )
​
      // The clicked element is `event.target`,
      // and its type is "button"
      .append( "the " + event.target.type + "." );
  }
};
​
var you = { type: "cat" };
var they = { type: "fish" };
​
// Set up handler to execute me.test() in the context
// of `me`, with `you` and `they` as additional arguments
var proxy = $.proxy( me.test, me, you, they );
​
$( "#test" )
  .on( "click", proxy );
</script>
​
</body>
</html>
```
     */
    proxy<TContext,
        TReturn,
        A, B, C,
        T, U, V>(funсtion: (this: TContext, a: A, b: B, c: C,
                            t: T, u: U, v: V) => TReturn,
                 context: TContext,
                 a: A, b: B, c: C): (t: T, u: U, v: V) => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @param b An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.4
     * @since 1.6
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     * @example ​ ````Change the context of functions bound to a click handler using the &quot;function, context&quot; signature. Unbind the first handler after first click.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  type: "zombie",
  test: function( event ) {
    // Without proxy, `this` would refer to the event target
    // use event.target to reference that element.
    var element = event.target;
    $( element ).css( "background-color", "red" );
​
    // With proxy, `this` refers to the me object encapsulating
    // this function.
    $( "#log" ).append( "Hello " + this.type + "<br>" );
    $( "#test" ).off( "click", this.test );
  }
};
​
var you = {
  type: "person",
  test: function( event ) {
    $( "#log" ).append( this.type + " " );
  }
};
​
// Execute you.test() in the context of the `you` object
// no matter where it is called
// i.e. the `this` keyword will refer to `you`
var youClick = $.proxy( you.test, you );
​
// attach click handlers to #test
$( "#test" )
  // this === "zombie"; handler unbound after first click
  .on( "click", $.proxy( me.test, me ) )
​
  // this === "person"
  .on( "click", youClick )
​
  // this === "zombie"
  .on( "click", $.proxy( you.test, me ) )
​
  // this === "<button> element"
  .on( "click", you.test );
</script>
​
</body>
</html>
```
     * @example ​ ````Change the context of a function bound to the click handler,
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  // I'm a dog
  type: "dog",
​
  // Note that event comes *after* one and two
  test: function( one, two, event ) {
    $( "#log" )
​
      // `one` maps to `you`, the 1st additional
      // argument in the $.proxy function call
      .append( "<h3>Hello " + one.type + ":</h3>" )
​
      // The `this` keyword refers to `me`
      // (the 2nd, context, argument of $.proxy)
      .append( "I am a " + this.type + ", " )
​
      // `two` maps to `they`, the 2nd additional
      // argument in the $.proxy function call
      .append( "and they are " + two.type + ".<br>" )
​
      // The event type is "click"
      .append( "Thanks for " + event.type + "ing." )
​
      // The clicked element is `event.target`,
      // and its type is "button"
      .append( "the " + event.target.type + "." );
  }
};
​
var you = { type: "cat" };
var they = { type: "fish" };
​
// Set up handler to execute me.test() in the context
// of `me`, with `you` and `they` as additional arguments
var proxy = $.proxy( me.test, me, you, they );
​
$( "#test" )
  .on( "click", proxy );
</script>
​
</body>
</html>
```
     */
    proxy<TContext,
        TReturn,
        A, B,
        T, U, V>(funсtion: (this: TContext, a: A, b: B,
                            t: T, u: U, v: V) => TReturn,
                 context: TContext,
                 a: A, b: B): (t: T, u: U, v: V) => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.4
     * @since 1.6
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     * @example ​ ````Change the context of functions bound to a click handler using the &quot;function, context&quot; signature. Unbind the first handler after first click.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  type: "zombie",
  test: function( event ) {
    // Without proxy, `this` would refer to the event target
    // use event.target to reference that element.
    var element = event.target;
    $( element ).css( "background-color", "red" );
​
    // With proxy, `this` refers to the me object encapsulating
    // this function.
    $( "#log" ).append( "Hello " + this.type + "<br>" );
    $( "#test" ).off( "click", this.test );
  }
};
​
var you = {
  type: "person",
  test: function( event ) {
    $( "#log" ).append( this.type + " " );
  }
};
​
// Execute you.test() in the context of the `you` object
// no matter where it is called
// i.e. the `this` keyword will refer to `you`
var youClick = $.proxy( you.test, you );
​
// attach click handlers to #test
$( "#test" )
  // this === "zombie"; handler unbound after first click
  .on( "click", $.proxy( me.test, me ) )
​
  // this === "person"
  .on( "click", youClick )
​
  // this === "zombie"
  .on( "click", $.proxy( you.test, me ) )
​
  // this === "<button> element"
  .on( "click", you.test );
</script>
​
</body>
</html>
```
     * @example ​ ````Change the context of a function bound to the click handler,
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  // I'm a dog
  type: "dog",
​
  // Note that event comes *after* one and two
  test: function( one, two, event ) {
    $( "#log" )
​
      // `one` maps to `you`, the 1st additional
      // argument in the $.proxy function call
      .append( "<h3>Hello " + one.type + ":</h3>" )
​
      // The `this` keyword refers to `me`
      // (the 2nd, context, argument of $.proxy)
      .append( "I am a " + this.type + ", " )
​
      // `two` maps to `they`, the 2nd additional
      // argument in the $.proxy function call
      .append( "and they are " + two.type + ".<br>" )
​
      // The event type is "click"
      .append( "Thanks for " + event.type + "ing." )
​
      // The clicked element is `event.target`,
      // and its type is "button"
      .append( "the " + event.target.type + "." );
  }
};
​
var you = { type: "cat" };
var they = { type: "fish" };
​
// Set up handler to execute me.test() in the context
// of `me`, with `you` and `they` as additional arguments
var proxy = $.proxy( me.test, me, you, they );
​
$( "#test" )
  .on( "click", proxy );
</script>
​
</body>
</html>
```
     */
    proxy<TContext,
        TReturn,
        A,
        T, U, V>(funсtion: (this: TContext, a: A,
                            t: T, u: U, v: V) => TReturn,
                 context: TContext,
                 a: A): (t: T, u: U, v: V) => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.4
     * @since 1.6
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     * @example ​ ````Change the context of functions bound to a click handler using the &quot;function, context&quot; signature. Unbind the first handler after first click.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  type: "zombie",
  test: function( event ) {
    // Without proxy, `this` would refer to the event target
    // use event.target to reference that element.
    var element = event.target;
    $( element ).css( "background-color", "red" );
​
    // With proxy, `this` refers to the me object encapsulating
    // this function.
    $( "#log" ).append( "Hello " + this.type + "<br>" );
    $( "#test" ).off( "click", this.test );
  }
};
​
var you = {
  type: "person",
  test: function( event ) {
    $( "#log" ).append( this.type + " " );
  }
};
​
// Execute you.test() in the context of the `you` object
// no matter where it is called
// i.e. the `this` keyword will refer to `you`
var youClick = $.proxy( you.test, you );
​
// attach click handlers to #test
$( "#test" )
  // this === "zombie"; handler unbound after first click
  .on( "click", $.proxy( me.test, me ) )
​
  // this === "person"
  .on( "click", youClick )
​
  // this === "zombie"
  .on( "click", $.proxy( you.test, me ) )
​
  // this === "<button> element"
  .on( "click", you.test );
</script>
​
</body>
</html>
```
     * @example ​ ````Change the context of a function bound to the click handler,
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  // I'm a dog
  type: "dog",
​
  // Note that event comes *after* one and two
  test: function( one, two, event ) {
    $( "#log" )
​
      // `one` maps to `you`, the 1st additional
      // argument in the $.proxy function call
      .append( "<h3>Hello " + one.type + ":</h3>" )
​
      // The `this` keyword refers to `me`
      // (the 2nd, context, argument of $.proxy)
      .append( "I am a " + this.type + ", " )
​
      // `two` maps to `they`, the 2nd additional
      // argument in the $.proxy function call
      .append( "and they are " + two.type + ".<br>" )
​
      // The event type is "click"
      .append( "Thanks for " + event.type + "ing." )
​
      // The clicked element is `event.target`,
      // and its type is "button"
      .append( "the " + event.target.type + "." );
  }
};
​
var you = { type: "cat" };
var they = { type: "fish" };
​
// Set up handler to execute me.test() in the context
// of `me`, with `you` and `they` as additional arguments
var proxy = $.proxy( me.test, me, you, they );
​
$( "#test" )
  .on( "click", proxy );
</script>
​
</body>
</html>
```
     */
    proxy<TContext,
        TReturn,
        T, U, V>(funсtion: (this: TContext, t: T, u: U, v: V) => TReturn,
                 context: TContext): (t: T, u: U, v: V) => TReturn;

    // #endregion

    // region 4 parameters
    // #region 4 parameters

    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @param b An argument to be passed to the function referenced in the `function` argument.
     * @param c An argument to be passed to the function referenced in the `function` argument.
     * @param d An argument to be passed to the function referenced in the `function` argument.
     * @param e An argument to be passed to the function referenced in the `function` argument.
     * @param f An argument to be passed to the function referenced in the `function` argument.
     * @param g An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.4
     * @since 1.6
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     * @example ​ ````Change the context of functions bound to a click handler using the &quot;function, context&quot; signature. Unbind the first handler after first click.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  type: "zombie",
  test: function( event ) {
    // Without proxy, `this` would refer to the event target
    // use event.target to reference that element.
    var element = event.target;
    $( element ).css( "background-color", "red" );
​
    // With proxy, `this` refers to the me object encapsulating
    // this function.
    $( "#log" ).append( "Hello " + this.type + "<br>" );
    $( "#test" ).off( "click", this.test );
  }
};
​
var you = {
  type: "person",
  test: function( event ) {
    $( "#log" ).append( this.type + " " );
  }
};
​
// Execute you.test() in the context of the `you` object
// no matter where it is called
// i.e. the `this` keyword will refer to `you`
var youClick = $.proxy( you.test, you );
​
// attach click handlers to #test
$( "#test" )
  // this === "zombie"; handler unbound after first click
  .on( "click", $.proxy( me.test, me ) )
​
  // this === "person"
  .on( "click", youClick )
​
  // this === "zombie"
  .on( "click", $.proxy( you.test, me ) )
​
  // this === "<button> element"
  .on( "click", you.test );
</script>
​
</body>
</html>
```
     * @example ​ ````Change the context of a function bound to the click handler,
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  // I'm a dog
  type: "dog",
​
  // Note that event comes *after* one and two
  test: function( one, two, event ) {
    $( "#log" )
​
      // `one` maps to `you`, the 1st additional
      // argument in the $.proxy function call
      .append( "<h3>Hello " + one.type + ":</h3>" )
​
      // The `this` keyword refers to `me`
      // (the 2nd, context, argument of $.proxy)
      .append( "I am a " + this.type + ", " )
​
      // `two` maps to `they`, the 2nd additional
      // argument in the $.proxy function call
      .append( "and they are " + two.type + ".<br>" )
​
      // The event type is "click"
      .append( "Thanks for " + event.type + "ing." )
​
      // The clicked element is `event.target`,
      // and its type is "button"
      .append( "the " + event.target.type + "." );
  }
};
​
var you = { type: "cat" };
var they = { type: "fish" };
​
// Set up handler to execute me.test() in the context
// of `me`, with `you` and `they` as additional arguments
var proxy = $.proxy( me.test, me, you, they );
​
$( "#test" )
  .on( "click", proxy );
</script>
​
</body>
</html>
```
     */
    proxy<TContext,
        TReturn,
        A, B, C, D, E, F, G,
        T, U, V, W>(funсtion: (this: TContext, a: A, b: B, c: C, d: D, e: E, f: F, g: G,
                               t: T, u: U, v: V, w: W) => TReturn,
                    context: TContext,
                    a: A, b: B, c: C, d: D, e: E, f: F, g: G): (t: T, u: U, v: V, w: W) => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @param b An argument to be passed to the function referenced in the `function` argument.
     * @param c An argument to be passed to the function referenced in the `function` argument.
     * @param d An argument to be passed to the function referenced in the `function` argument.
     * @param e An argument to be passed to the function referenced in the `function` argument.
     * @param f An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.4
     * @since 1.6
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     * @example ​ ````Change the context of functions bound to a click handler using the &quot;function, context&quot; signature. Unbind the first handler after first click.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  type: "zombie",
  test: function( event ) {
    // Without proxy, `this` would refer to the event target
    // use event.target to reference that element.
    var element = event.target;
    $( element ).css( "background-color", "red" );
​
    // With proxy, `this` refers to the me object encapsulating
    // this function.
    $( "#log" ).append( "Hello " + this.type + "<br>" );
    $( "#test" ).off( "click", this.test );
  }
};
​
var you = {
  type: "person",
  test: function( event ) {
    $( "#log" ).append( this.type + " " );
  }
};
​
// Execute you.test() in the context of the `you` object
// no matter where it is called
// i.e. the `this` keyword will refer to `you`
var youClick = $.proxy( you.test, you );
​
// attach click handlers to #test
$( "#test" )
  // this === "zombie"; handler unbound after first click
  .on( "click", $.proxy( me.test, me ) )
​
  // this === "person"
  .on( "click", youClick )
​
  // this === "zombie"
  .on( "click", $.proxy( you.test, me ) )
​
  // this === "<button> element"
  .on( "click", you.test );
</script>
​
</body>
</html>
```
     * @example ​ ````Change the context of a function bound to the click handler,
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  // I'm a dog
  type: "dog",
​
  // Note that event comes *after* one and two
  test: function( one, two, event ) {
    $( "#log" )
​
      // `one` maps to `you`, the 1st additional
      // argument in the $.proxy function call
      .append( "<h3>Hello " + one.type + ":</h3>" )
​
      // The `this` keyword refers to `me`
      // (the 2nd, context, argument of $.proxy)
      .append( "I am a " + this.type + ", " )
​
      // `two` maps to `they`, the 2nd additional
      // argument in the $.proxy function call
      .append( "and they are " + two.type + ".<br>" )
​
      // The event type is "click"
      .append( "Thanks for " + event.type + "ing." )
​
      // The clicked element is `event.target`,
      // and its type is "button"
      .append( "the " + event.target.type + "." );
  }
};
​
var you = { type: "cat" };
var they = { type: "fish" };
​
// Set up handler to execute me.test() in the context
// of `me`, with `you` and `they` as additional arguments
var proxy = $.proxy( me.test, me, you, they );
​
$( "#test" )
  .on( "click", proxy );
</script>
​
</body>
</html>
```
     */
    proxy<TContext,
        TReturn,
        A, B, C, D, E, F,
        T, U, V, W>(funсtion: (this: TContext, a: A, b: B, c: C, d: D, e: E, f: F,
                               t: T, u: U, v: V, w: W) => TReturn,
                    context: TContext,
                    a: A, b: B, c: C, d: D, e: E, f: F): (t: T, u: U, v: V, w: W) => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @param b An argument to be passed to the function referenced in the `function` argument.
     * @param c An argument to be passed to the function referenced in the `function` argument.
     * @param d An argument to be passed to the function referenced in the `function` argument.
     * @param e An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.4
     * @since 1.6
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     * @example ​ ````Change the context of functions bound to a click handler using the &quot;function, context&quot; signature. Unbind the first handler after first click.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  type: "zombie",
  test: function( event ) {
    // Without proxy, `this` would refer to the event target
    // use event.target to reference that element.
    var element = event.target;
    $( element ).css( "background-color", "red" );
​
    // With proxy, `this` refers to the me object encapsulating
    // this function.
    $( "#log" ).append( "Hello " + this.type + "<br>" );
    $( "#test" ).off( "click", this.test );
  }
};
​
var you = {
  type: "person",
  test: function( event ) {
    $( "#log" ).append( this.type + " " );
  }
};
​
// Execute you.test() in the context of the `you` object
// no matter where it is called
// i.e. the `this` keyword will refer to `you`
var youClick = $.proxy( you.test, you );
​
// attach click handlers to #test
$( "#test" )
  // this === "zombie"; handler unbound after first click
  .on( "click", $.proxy( me.test, me ) )
​
  // this === "person"
  .on( "click", youClick )
​
  // this === "zombie"
  .on( "click", $.proxy( you.test, me ) )
​
  // this === "<button> element"
  .on( "click", you.test );
</script>
​
</body>
</html>
```
     * @example ​ ````Change the context of a function bound to the click handler,
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  // I'm a dog
  type: "dog",
​
  // Note that event comes *after* one and two
  test: function( one, two, event ) {
    $( "#log" )
​
      // `one` maps to `you`, the 1st additional
      // argument in the $.proxy function call
      .append( "<h3>Hello " + one.type + ":</h3>" )
​
      // The `this` keyword refers to `me`
      // (the 2nd, context, argument of $.proxy)
      .append( "I am a " + this.type + ", " )
​
      // `two` maps to `they`, the 2nd additional
      // argument in the $.proxy function call
      .append( "and they are " + two.type + ".<br>" )
​
      // The event type is "click"
      .append( "Thanks for " + event.type + "ing." )
​
      // The clicked element is `event.target`,
      // and its type is "button"
      .append( "the " + event.target.type + "." );
  }
};
​
var you = { type: "cat" };
var they = { type: "fish" };
​
// Set up handler to execute me.test() in the context
// of `me`, with `you` and `they` as additional arguments
var proxy = $.proxy( me.test, me, you, they );
​
$( "#test" )
  .on( "click", proxy );
</script>
​
</body>
</html>
```
     */
    proxy<TContext,
        TReturn,
        A, B, C, D, E,
        T, U, V, W>(funсtion: (this: TContext, a: A, b: B, c: C, d: D, e: E,
                               t: T, u: U, v: V, w: W) => TReturn,
                    context: TContext,
                    a: A, b: B, c: C, d: D, e: E): (t: T, u: U, v: V, w: W) => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @param b An argument to be passed to the function referenced in the `function` argument.
     * @param c An argument to be passed to the function referenced in the `function` argument.
     * @param d An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.4
     * @since 1.6
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     * @example ​ ````Change the context of functions bound to a click handler using the &quot;function, context&quot; signature. Unbind the first handler after first click.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  type: "zombie",
  test: function( event ) {
    // Without proxy, `this` would refer to the event target
    // use event.target to reference that element.
    var element = event.target;
    $( element ).css( "background-color", "red" );
​
    // With proxy, `this` refers to the me object encapsulating
    // this function.
    $( "#log" ).append( "Hello " + this.type + "<br>" );
    $( "#test" ).off( "click", this.test );
  }
};
​
var you = {
  type: "person",
  test: function( event ) {
    $( "#log" ).append( this.type + " " );
  }
};
​
// Execute you.test() in the context of the `you` object
// no matter where it is called
// i.e. the `this` keyword will refer to `you`
var youClick = $.proxy( you.test, you );
​
// attach click handlers to #test
$( "#test" )
  // this === "zombie"; handler unbound after first click
  .on( "click", $.proxy( me.test, me ) )
​
  // this === "person"
  .on( "click", youClick )
​
  // this === "zombie"
  .on( "click", $.proxy( you.test, me ) )
​
  // this === "<button> element"
  .on( "click", you.test );
</script>
​
</body>
</html>
```
     * @example ​ ````Change the context of a function bound to the click handler,
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  // I'm a dog
  type: "dog",
​
  // Note that event comes *after* one and two
  test: function( one, two, event ) {
    $( "#log" )
​
      // `one` maps to `you`, the 1st additional
      // argument in the $.proxy function call
      .append( "<h3>Hello " + one.type + ":</h3>" )
​
      // The `this` keyword refers to `me`
      // (the 2nd, context, argument of $.proxy)
      .append( "I am a " + this.type + ", " )
​
      // `two` maps to `they`, the 2nd additional
      // argument in the $.proxy function call
      .append( "and they are " + two.type + ".<br>" )
​
      // The event type is "click"
      .append( "Thanks for " + event.type + "ing." )
​
      // The clicked element is `event.target`,
      // and its type is "button"
      .append( "the " + event.target.type + "." );
  }
};
​
var you = { type: "cat" };
var they = { type: "fish" };
​
// Set up handler to execute me.test() in the context
// of `me`, with `you` and `they` as additional arguments
var proxy = $.proxy( me.test, me, you, they );
​
$( "#test" )
  .on( "click", proxy );
</script>
​
</body>
</html>
```
     */
    proxy<TContext,
        TReturn,
        A, B, C, D,
        T, U, V, W>(funсtion: (this: TContext, a: A, b: B, c: C, d: D,
                               t: T, u: U, v: V, w: W) => TReturn,
                    context: TContext,
                    a: A, b: B, c: C, d: D): (t: T, u: U, v: V, w: W) => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @param b An argument to be passed to the function referenced in the `function` argument.
     * @param c An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.4
     * @since 1.6
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     * @example ​ ````Change the context of functions bound to a click handler using the &quot;function, context&quot; signature. Unbind the first handler after first click.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  type: "zombie",
  test: function( event ) {
    // Without proxy, `this` would refer to the event target
    // use event.target to reference that element.
    var element = event.target;
    $( element ).css( "background-color", "red" );
​
    // With proxy, `this` refers to the me object encapsulating
    // this function.
    $( "#log" ).append( "Hello " + this.type + "<br>" );
    $( "#test" ).off( "click", this.test );
  }
};
​
var you = {
  type: "person",
  test: function( event ) {
    $( "#log" ).append( this.type + " " );
  }
};
​
// Execute you.test() in the context of the `you` object
// no matter where it is called
// i.e. the `this` keyword will refer to `you`
var youClick = $.proxy( you.test, you );
​
// attach click handlers to #test
$( "#test" )
  // this === "zombie"; handler unbound after first click
  .on( "click", $.proxy( me.test, me ) )
​
  // this === "person"
  .on( "click", youClick )
​
  // this === "zombie"
  .on( "click", $.proxy( you.test, me ) )
​
  // this === "<button> element"
  .on( "click", you.test );
</script>
​
</body>
</html>
```
     * @example ​ ````Change the context of a function bound to the click handler,
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  // I'm a dog
  type: "dog",
​
  // Note that event comes *after* one and two
  test: function( one, two, event ) {
    $( "#log" )
​
      // `one` maps to `you`, the 1st additional
      // argument in the $.proxy function call
      .append( "<h3>Hello " + one.type + ":</h3>" )
​
      // The `this` keyword refers to `me`
      // (the 2nd, context, argument of $.proxy)
      .append( "I am a " + this.type + ", " )
​
      // `two` maps to `they`, the 2nd additional
      // argument in the $.proxy function call
      .append( "and they are " + two.type + ".<br>" )
​
      // The event type is "click"
      .append( "Thanks for " + event.type + "ing." )
​
      // The clicked element is `event.target`,
      // and its type is "button"
      .append( "the " + event.target.type + "." );
  }
};
​
var you = { type: "cat" };
var they = { type: "fish" };
​
// Set up handler to execute me.test() in the context
// of `me`, with `you` and `they` as additional arguments
var proxy = $.proxy( me.test, me, you, they );
​
$( "#test" )
  .on( "click", proxy );
</script>
​
</body>
</html>
```
     */
    proxy<TContext,
        TReturn,
        A, B, C,
        T, U, V, W>(funсtion: (this: TContext, a: A, b: B, c: C,
                               t: T, u: U, v: V, w: W) => TReturn,
                    context: TContext,
                    a: A, b: B, c: C): (t: T, u: U, v: V, w: W) => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @param b An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.4
     * @since 1.6
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     * @example ​ ````Change the context of functions bound to a click handler using the &quot;function, context&quot; signature. Unbind the first handler after first click.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  type: "zombie",
  test: function( event ) {
    // Without proxy, `this` would refer to the event target
    // use event.target to reference that element.
    var element = event.target;
    $( element ).css( "background-color", "red" );
​
    // With proxy, `this` refers to the me object encapsulating
    // this function.
    $( "#log" ).append( "Hello " + this.type + "<br>" );
    $( "#test" ).off( "click", this.test );
  }
};
​
var you = {
  type: "person",
  test: function( event ) {
    $( "#log" ).append( this.type + " " );
  }
};
​
// Execute you.test() in the context of the `you` object
// no matter where it is called
// i.e. the `this` keyword will refer to `you`
var youClick = $.proxy( you.test, you );
​
// attach click handlers to #test
$( "#test" )
  // this === "zombie"; handler unbound after first click
  .on( "click", $.proxy( me.test, me ) )
​
  // this === "person"
  .on( "click", youClick )
​
  // this === "zombie"
  .on( "click", $.proxy( you.test, me ) )
​
  // this === "<button> element"
  .on( "click", you.test );
</script>
​
</body>
</html>
```
     * @example ​ ````Change the context of a function bound to the click handler,
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  // I'm a dog
  type: "dog",
​
  // Note that event comes *after* one and two
  test: function( one, two, event ) {
    $( "#log" )
​
      // `one` maps to `you`, the 1st additional
      // argument in the $.proxy function call
      .append( "<h3>Hello " + one.type + ":</h3>" )
​
      // The `this` keyword refers to `me`
      // (the 2nd, context, argument of $.proxy)
      .append( "I am a " + this.type + ", " )
​
      // `two` maps to `they`, the 2nd additional
      // argument in the $.proxy function call
      .append( "and they are " + two.type + ".<br>" )
​
      // The event type is "click"
      .append( "Thanks for " + event.type + "ing." )
​
      // The clicked element is `event.target`,
      // and its type is "button"
      .append( "the " + event.target.type + "." );
  }
};
​
var you = { type: "cat" };
var they = { type: "fish" };
​
// Set up handler to execute me.test() in the context
// of `me`, with `you` and `they` as additional arguments
var proxy = $.proxy( me.test, me, you, they );
​
$( "#test" )
  .on( "click", proxy );
</script>
​
</body>
</html>
```
     */
    proxy<TContext,
        TReturn,
        A, B,
        T, U, V, W>(funсtion: (this: TContext, a: A, b: B,
                               t: T, u: U, v: V, w: W) => TReturn,
                    context: TContext,
                    a: A, b: B): (t: T, u: U, v: V, w: W) => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.4
     * @since 1.6
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     * @example ​ ````Change the context of functions bound to a click handler using the &quot;function, context&quot; signature. Unbind the first handler after first click.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  type: "zombie",
  test: function( event ) {
    // Without proxy, `this` would refer to the event target
    // use event.target to reference that element.
    var element = event.target;
    $( element ).css( "background-color", "red" );
​
    // With proxy, `this` refers to the me object encapsulating
    // this function.
    $( "#log" ).append( "Hello " + this.type + "<br>" );
    $( "#test" ).off( "click", this.test );
  }
};
​
var you = {
  type: "person",
  test: function( event ) {
    $( "#log" ).append( this.type + " " );
  }
};
​
// Execute you.test() in the context of the `you` object
// no matter where it is called
// i.e. the `this` keyword will refer to `you`
var youClick = $.proxy( you.test, you );
​
// attach click handlers to #test
$( "#test" )
  // this === "zombie"; handler unbound after first click
  .on( "click", $.proxy( me.test, me ) )
​
  // this === "person"
  .on( "click", youClick )
​
  // this === "zombie"
  .on( "click", $.proxy( you.test, me ) )
​
  // this === "<button> element"
  .on( "click", you.test );
</script>
​
</body>
</html>
```
     * @example ​ ````Change the context of a function bound to the click handler,
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  // I'm a dog
  type: "dog",
​
  // Note that event comes *after* one and two
  test: function( one, two, event ) {
    $( "#log" )
​
      // `one` maps to `you`, the 1st additional
      // argument in the $.proxy function call
      .append( "<h3>Hello " + one.type + ":</h3>" )
​
      // The `this` keyword refers to `me`
      // (the 2nd, context, argument of $.proxy)
      .append( "I am a " + this.type + ", " )
​
      // `two` maps to `they`, the 2nd additional
      // argument in the $.proxy function call
      .append( "and they are " + two.type + ".<br>" )
​
      // The event type is "click"
      .append( "Thanks for " + event.type + "ing." )
​
      // The clicked element is `event.target`,
      // and its type is "button"
      .append( "the " + event.target.type + "." );
  }
};
​
var you = { type: "cat" };
var they = { type: "fish" };
​
// Set up handler to execute me.test() in the context
// of `me`, with `you` and `they` as additional arguments
var proxy = $.proxy( me.test, me, you, they );
​
$( "#test" )
  .on( "click", proxy );
</script>
​
</body>
</html>
```
     */
    proxy<TContext,
        TReturn,
        A,
        T, U, V, W>(funсtion: (this: TContext, a: A,
                               t: T, u: U, v: V, w: W) => TReturn,
                    context: TContext,
                    a: A): (t: T, u: U, v: V, w: W) => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.4
     * @since 1.6
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     * @example ​ ````Change the context of functions bound to a click handler using the &quot;function, context&quot; signature. Unbind the first handler after first click.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  type: "zombie",
  test: function( event ) {
    // Without proxy, `this` would refer to the event target
    // use event.target to reference that element.
    var element = event.target;
    $( element ).css( "background-color", "red" );
​
    // With proxy, `this` refers to the me object encapsulating
    // this function.
    $( "#log" ).append( "Hello " + this.type + "<br>" );
    $( "#test" ).off( "click", this.test );
  }
};
​
var you = {
  type: "person",
  test: function( event ) {
    $( "#log" ).append( this.type + " " );
  }
};
​
// Execute you.test() in the context of the `you` object
// no matter where it is called
// i.e. the `this` keyword will refer to `you`
var youClick = $.proxy( you.test, you );
​
// attach click handlers to #test
$( "#test" )
  // this === "zombie"; handler unbound after first click
  .on( "click", $.proxy( me.test, me ) )
​
  // this === "person"
  .on( "click", youClick )
​
  // this === "zombie"
  .on( "click", $.proxy( you.test, me ) )
​
  // this === "<button> element"
  .on( "click", you.test );
</script>
​
</body>
</html>
```
     * @example ​ ````Change the context of a function bound to the click handler,
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  // I'm a dog
  type: "dog",
​
  // Note that event comes *after* one and two
  test: function( one, two, event ) {
    $( "#log" )
​
      // `one` maps to `you`, the 1st additional
      // argument in the $.proxy function call
      .append( "<h3>Hello " + one.type + ":</h3>" )
​
      // The `this` keyword refers to `me`
      // (the 2nd, context, argument of $.proxy)
      .append( "I am a " + this.type + ", " )
​
      // `two` maps to `they`, the 2nd additional
      // argument in the $.proxy function call
      .append( "and they are " + two.type + ".<br>" )
​
      // The event type is "click"
      .append( "Thanks for " + event.type + "ing." )
​
      // The clicked element is `event.target`,
      // and its type is "button"
      .append( "the " + event.target.type + "." );
  }
};
​
var you = { type: "cat" };
var they = { type: "fish" };
​
// Set up handler to execute me.test() in the context
// of `me`, with `you` and `they` as additional arguments
var proxy = $.proxy( me.test, me, you, they );
​
$( "#test" )
  .on( "click", proxy );
</script>
​
</body>
</html>
```
     */
    proxy<TContext,
        TReturn,
        T, U, V, W>(funсtion: (this: TContext, t: T, u: U, v: V, w: W) => TReturn,
                    context: TContext): (t: T, u: U, v: V, w: W) => TReturn;

    // #endregion

    // region 5 parameters
    // #region 5 parameters

    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @param b An argument to be passed to the function referenced in the `function` argument.
     * @param c An argument to be passed to the function referenced in the `function` argument.
     * @param d An argument to be passed to the function referenced in the `function` argument.
     * @param e An argument to be passed to the function referenced in the `function` argument.
     * @param f An argument to be passed to the function referenced in the `function` argument.
     * @param g An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.4
     * @since 1.6
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     * @example ​ ````Change the context of functions bound to a click handler using the &quot;function, context&quot; signature. Unbind the first handler after first click.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  type: "zombie",
  test: function( event ) {
    // Without proxy, `this` would refer to the event target
    // use event.target to reference that element.
    var element = event.target;
    $( element ).css( "background-color", "red" );
​
    // With proxy, `this` refers to the me object encapsulating
    // this function.
    $( "#log" ).append( "Hello " + this.type + "<br>" );
    $( "#test" ).off( "click", this.test );
  }
};
​
var you = {
  type: "person",
  test: function( event ) {
    $( "#log" ).append( this.type + " " );
  }
};
​
// Execute you.test() in the context of the `you` object
// no matter where it is called
// i.e. the `this` keyword will refer to `you`
var youClick = $.proxy( you.test, you );
​
// attach click handlers to #test
$( "#test" )
  // this === "zombie"; handler unbound after first click
  .on( "click", $.proxy( me.test, me ) )
​
  // this === "person"
  .on( "click", youClick )
​
  // this === "zombie"
  .on( "click", $.proxy( you.test, me ) )
​
  // this === "<button> element"
  .on( "click", you.test );
</script>
​
</body>
</html>
```
     * @example ​ ````Change the context of a function bound to the click handler,
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  // I'm a dog
  type: "dog",
​
  // Note that event comes *after* one and two
  test: function( one, two, event ) {
    $( "#log" )
​
      // `one` maps to `you`, the 1st additional
      // argument in the $.proxy function call
      .append( "<h3>Hello " + one.type + ":</h3>" )
​
      // The `this` keyword refers to `me`
      // (the 2nd, context, argument of $.proxy)
      .append( "I am a " + this.type + ", " )
​
      // `two` maps to `they`, the 2nd additional
      // argument in the $.proxy function call
      .append( "and they are " + two.type + ".<br>" )
​
      // The event type is "click"
      .append( "Thanks for " + event.type + "ing." )
​
      // The clicked element is `event.target`,
      // and its type is "button"
      .append( "the " + event.target.type + "." );
  }
};
​
var you = { type: "cat" };
var they = { type: "fish" };
​
// Set up handler to execute me.test() in the context
// of `me`, with `you` and `they` as additional arguments
var proxy = $.proxy( me.test, me, you, they );
​
$( "#test" )
  .on( "click", proxy );
</script>
​
</body>
</html>
```
     */
    proxy<TContext,
        TReturn,
        A, B, C, D, E, F, G,
        T, U, V, W, X>(funсtion: (this: TContext, a: A, b: B, c: C, d: D, e: E, f: F, g: G,
                                  t: T, u: U, v: V, w: W, x: X) => TReturn,
                       context: TContext,
                       a: A, b: B, c: C, d: D, e: E, f: F, g: G): (t: T, u: U, v: V, w: W, x: X) => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @param b An argument to be passed to the function referenced in the `function` argument.
     * @param c An argument to be passed to the function referenced in the `function` argument.
     * @param d An argument to be passed to the function referenced in the `function` argument.
     * @param e An argument to be passed to the function referenced in the `function` argument.
     * @param f An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.4
     * @since 1.6
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     * @example ​ ````Change the context of functions bound to a click handler using the &quot;function, context&quot; signature. Unbind the first handler after first click.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  type: "zombie",
  test: function( event ) {
    // Without proxy, `this` would refer to the event target
    // use event.target to reference that element.
    var element = event.target;
    $( element ).css( "background-color", "red" );
​
    // With proxy, `this` refers to the me object encapsulating
    // this function.
    $( "#log" ).append( "Hello " + this.type + "<br>" );
    $( "#test" ).off( "click", this.test );
  }
};
​
var you = {
  type: "person",
  test: function( event ) {
    $( "#log" ).append( this.type + " " );
  }
};
​
// Execute you.test() in the context of the `you` object
// no matter where it is called
// i.e. the `this` keyword will refer to `you`
var youClick = $.proxy( you.test, you );
​
// attach click handlers to #test
$( "#test" )
  // this === "zombie"; handler unbound after first click
  .on( "click", $.proxy( me.test, me ) )
​
  // this === "person"
  .on( "click", youClick )
​
  // this === "zombie"
  .on( "click", $.proxy( you.test, me ) )
​
  // this === "<button> element"
  .on( "click", you.test );
</script>
​
</body>
</html>
```
     * @example ​ ````Change the context of a function bound to the click handler,
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  // I'm a dog
  type: "dog",
​
  // Note that event comes *after* one and two
  test: function( one, two, event ) {
    $( "#log" )
​
      // `one` maps to `you`, the 1st additional
      // argument in the $.proxy function call
      .append( "<h3>Hello " + one.type + ":</h3>" )
​
      // The `this` keyword refers to `me`
      // (the 2nd, context, argument of $.proxy)
      .append( "I am a " + this.type + ", " )
​
      // `two` maps to `they`, the 2nd additional
      // argument in the $.proxy function call
      .append( "and they are " + two.type + ".<br>" )
​
      // The event type is "click"
      .append( "Thanks for " + event.type + "ing." )
​
      // The clicked element is `event.target`,
      // and its type is "button"
      .append( "the " + event.target.type + "." );
  }
};
​
var you = { type: "cat" };
var they = { type: "fish" };
​
// Set up handler to execute me.test() in the context
// of `me`, with `you` and `they` as additional arguments
var proxy = $.proxy( me.test, me, you, they );
​
$( "#test" )
  .on( "click", proxy );
</script>
​
</body>
</html>
```
     */
    proxy<TContext,
        TReturn,
        A, B, C, D, E, F,
        T, U, V, W, X>(funсtion: (this: TContext, a: A, b: B, c: C, d: D, e: E, f: F,
                                  t: T, u: U, v: V, w: W, x: X) => TReturn,
                       context: TContext,
                       a: A, b: B, c: C, d: D, e: E, f: F): (t: T, u: U, v: V, w: W, x: X) => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @param b An argument to be passed to the function referenced in the `function` argument.
     * @param c An argument to be passed to the function referenced in the `function` argument.
     * @param d An argument to be passed to the function referenced in the `function` argument.
     * @param e An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.4
     * @since 1.6
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     * @example ​ ````Change the context of functions bound to a click handler using the &quot;function, context&quot; signature. Unbind the first handler after first click.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  type: "zombie",
  test: function( event ) {
    // Without proxy, `this` would refer to the event target
    // use event.target to reference that element.
    var element = event.target;
    $( element ).css( "background-color", "red" );
​
    // With proxy, `this` refers to the me object encapsulating
    // this function.
    $( "#log" ).append( "Hello " + this.type + "<br>" );
    $( "#test" ).off( "click", this.test );
  }
};
​
var you = {
  type: "person",
  test: function( event ) {
    $( "#log" ).append( this.type + " " );
  }
};
​
// Execute you.test() in the context of the `you` object
// no matter where it is called
// i.e. the `this` keyword will refer to `you`
var youClick = $.proxy( you.test, you );
​
// attach click handlers to #test
$( "#test" )
  // this === "zombie"; handler unbound after first click
  .on( "click", $.proxy( me.test, me ) )
​
  // this === "person"
  .on( "click", youClick )
​
  // this === "zombie"
  .on( "click", $.proxy( you.test, me ) )
​
  // this === "<button> element"
  .on( "click", you.test );
</script>
​
</body>
</html>
```
     * @example ​ ````Change the context of a function bound to the click handler,
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  // I'm a dog
  type: "dog",
​
  // Note that event comes *after* one and two
  test: function( one, two, event ) {
    $( "#log" )
​
      // `one` maps to `you`, the 1st additional
      // argument in the $.proxy function call
      .append( "<h3>Hello " + one.type + ":</h3>" )
​
      // The `this` keyword refers to `me`
      // (the 2nd, context, argument of $.proxy)
      .append( "I am a " + this.type + ", " )
​
      // `two` maps to `they`, the 2nd additional
      // argument in the $.proxy function call
      .append( "and they are " + two.type + ".<br>" )
​
      // The event type is "click"
      .append( "Thanks for " + event.type + "ing." )
​
      // The clicked element is `event.target`,
      // and its type is "button"
      .append( "the " + event.target.type + "." );
  }
};
​
var you = { type: "cat" };
var they = { type: "fish" };
​
// Set up handler to execute me.test() in the context
// of `me`, with `you` and `they` as additional arguments
var proxy = $.proxy( me.test, me, you, they );
​
$( "#test" )
  .on( "click", proxy );
</script>
​
</body>
</html>
```
     */
    proxy<TContext,
        TReturn,
        A, B, C, D, E,
        T, U, V, W, X>(funсtion: (this: TContext, a: A, b: B, c: C, d: D, e: E,
                                  t: T, u: U, v: V, w: W, x: X) => TReturn,
                       context: TContext,
                       a: A, b: B, c: C, d: D, e: E): (t: T, u: U, v: V, w: W, x: X) => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @param b An argument to be passed to the function referenced in the `function` argument.
     * @param c An argument to be passed to the function referenced in the `function` argument.
     * @param d An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.4
     * @since 1.6
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     * @example ​ ````Change the context of functions bound to a click handler using the &quot;function, context&quot; signature. Unbind the first handler after first click.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  type: "zombie",
  test: function( event ) {
    // Without proxy, `this` would refer to the event target
    // use event.target to reference that element.
    var element = event.target;
    $( element ).css( "background-color", "red" );
​
    // With proxy, `this` refers to the me object encapsulating
    // this function.
    $( "#log" ).append( "Hello " + this.type + "<br>" );
    $( "#test" ).off( "click", this.test );
  }
};
​
var you = {
  type: "person",
  test: function( event ) {
    $( "#log" ).append( this.type + " " );
  }
};
​
// Execute you.test() in the context of the `you` object
// no matter where it is called
// i.e. the `this` keyword will refer to `you`
var youClick = $.proxy( you.test, you );
​
// attach click handlers to #test
$( "#test" )
  // this === "zombie"; handler unbound after first click
  .on( "click", $.proxy( me.test, me ) )
​
  // this === "person"
  .on( "click", youClick )
​
  // this === "zombie"
  .on( "click", $.proxy( you.test, me ) )
​
  // this === "<button> element"
  .on( "click", you.test );
</script>
​
</body>
</html>
```
     * @example ​ ````Change the context of a function bound to the click handler,
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  // I'm a dog
  type: "dog",
​
  // Note that event comes *after* one and two
  test: function( one, two, event ) {
    $( "#log" )
​
      // `one` maps to `you`, the 1st additional
      // argument in the $.proxy function call
      .append( "<h3>Hello " + one.type + ":</h3>" )
​
      // The `this` keyword refers to `me`
      // (the 2nd, context, argument of $.proxy)
      .append( "I am a " + this.type + ", " )
​
      // `two` maps to `they`, the 2nd additional
      // argument in the $.proxy function call
      .append( "and they are " + two.type + ".<br>" )
​
      // The event type is "click"
      .append( "Thanks for " + event.type + "ing." )
​
      // The clicked element is `event.target`,
      // and its type is "button"
      .append( "the " + event.target.type + "." );
  }
};
​
var you = { type: "cat" };
var they = { type: "fish" };
​
// Set up handler to execute me.test() in the context
// of `me`, with `you` and `they` as additional arguments
var proxy = $.proxy( me.test, me, you, they );
​
$( "#test" )
  .on( "click", proxy );
</script>
​
</body>
</html>
```
     */
    proxy<TContext,
        TReturn,
        A, B, C, D,
        T, U, V, W, X>(funсtion: (this: TContext, a: A, b: B, c: C, d: D,
                                  t: T, u: U, v: V, w: W, x: X) => TReturn,
                       context: TContext,
                       a: A, b: B, c: C, d: D): (t: T, u: U, v: V, w: W, x: X) => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @param b An argument to be passed to the function referenced in the `function` argument.
     * @param c An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.4
     * @since 1.6
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     * @example ​ ````Change the context of functions bound to a click handler using the &quot;function, context&quot; signature. Unbind the first handler after first click.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  type: "zombie",
  test: function( event ) {
    // Without proxy, `this` would refer to the event target
    // use event.target to reference that element.
    var element = event.target;
    $( element ).css( "background-color", "red" );
​
    // With proxy, `this` refers to the me object encapsulating
    // this function.
    $( "#log" ).append( "Hello " + this.type + "<br>" );
    $( "#test" ).off( "click", this.test );
  }
};
​
var you = {
  type: "person",
  test: function( event ) {
    $( "#log" ).append( this.type + " " );
  }
};
​
// Execute you.test() in the context of the `you` object
// no matter where it is called
// i.e. the `this` keyword will refer to `you`
var youClick = $.proxy( you.test, you );
​
// attach click handlers to #test
$( "#test" )
  // this === "zombie"; handler unbound after first click
  .on( "click", $.proxy( me.test, me ) )
​
  // this === "person"
  .on( "click", youClick )
​
  // this === "zombie"
  .on( "click", $.proxy( you.test, me ) )
​
  // this === "<button> element"
  .on( "click", you.test );
</script>
​
</body>
</html>
```
     * @example ​ ````Change the context of a function bound to the click handler,
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  // I'm a dog
  type: "dog",
​
  // Note that event comes *after* one and two
  test: function( one, two, event ) {
    $( "#log" )
​
      // `one` maps to `you`, the 1st additional
      // argument in the $.proxy function call
      .append( "<h3>Hello " + one.type + ":</h3>" )
​
      // The `this` keyword refers to `me`
      // (the 2nd, context, argument of $.proxy)
      .append( "I am a " + this.type + ", " )
​
      // `two` maps to `they`, the 2nd additional
      // argument in the $.proxy function call
      .append( "and they are " + two.type + ".<br>" )
​
      // The event type is "click"
      .append( "Thanks for " + event.type + "ing." )
​
      // The clicked element is `event.target`,
      // and its type is "button"
      .append( "the " + event.target.type + "." );
  }
};
​
var you = { type: "cat" };
var they = { type: "fish" };
​
// Set up handler to execute me.test() in the context
// of `me`, with `you` and `they` as additional arguments
var proxy = $.proxy( me.test, me, you, they );
​
$( "#test" )
  .on( "click", proxy );
</script>
​
</body>
</html>
```
     */
    proxy<TContext,
        TReturn,
        A, B, C,
        T, U, V, W, X>(funсtion: (this: TContext, a: A, b: B, c: C,
                                  t: T, u: U, v: V, w: W, x: X) => TReturn,
                       context: TContext,
                       a: A, b: B, c: C): (t: T, u: U, v: V, w: W, x: X) => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @param b An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.4
     * @since 1.6
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     * @example ​ ````Change the context of functions bound to a click handler using the &quot;function, context&quot; signature. Unbind the first handler after first click.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  type: "zombie",
  test: function( event ) {
    // Without proxy, `this` would refer to the event target
    // use event.target to reference that element.
    var element = event.target;
    $( element ).css( "background-color", "red" );
​
    // With proxy, `this` refers to the me object encapsulating
    // this function.
    $( "#log" ).append( "Hello " + this.type + "<br>" );
    $( "#test" ).off( "click", this.test );
  }
};
​
var you = {
  type: "person",
  test: function( event ) {
    $( "#log" ).append( this.type + " " );
  }
};
​
// Execute you.test() in the context of the `you` object
// no matter where it is called
// i.e. the `this` keyword will refer to `you`
var youClick = $.proxy( you.test, you );
​
// attach click handlers to #test
$( "#test" )
  // this === "zombie"; handler unbound after first click
  .on( "click", $.proxy( me.test, me ) )
​
  // this === "person"
  .on( "click", youClick )
​
  // this === "zombie"
  .on( "click", $.proxy( you.test, me ) )
​
  // this === "<button> element"
  .on( "click", you.test );
</script>
​
</body>
</html>
```
     * @example ​ ````Change the context of a function bound to the click handler,
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  // I'm a dog
  type: "dog",
​
  // Note that event comes *after* one and two
  test: function( one, two, event ) {
    $( "#log" )
​
      // `one` maps to `you`, the 1st additional
      // argument in the $.proxy function call
      .append( "<h3>Hello " + one.type + ":</h3>" )
​
      // The `this` keyword refers to `me`
      // (the 2nd, context, argument of $.proxy)
      .append( "I am a " + this.type + ", " )
​
      // `two` maps to `they`, the 2nd additional
      // argument in the $.proxy function call
      .append( "and they are " + two.type + ".<br>" )
​
      // The event type is "click"
      .append( "Thanks for " + event.type + "ing." )
​
      // The clicked element is `event.target`,
      // and its type is "button"
      .append( "the " + event.target.type + "." );
  }
};
​
var you = { type: "cat" };
var they = { type: "fish" };
​
// Set up handler to execute me.test() in the context
// of `me`, with `you` and `they` as additional arguments
var proxy = $.proxy( me.test, me, you, they );
​
$( "#test" )
  .on( "click", proxy );
</script>
​
</body>
</html>
```
     */
    proxy<TContext,
        TReturn,
        A, B,
        T, U, V, W, X>(funсtion: (this: TContext, a: A, b: B,
                                  t: T, u: U, v: V, w: W, x: X) => TReturn,
                       context: TContext,
                       a: A, b: B): (t: T, u: U, v: V, w: W, x: X) => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.4
     * @since 1.6
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     * @example ​ ````Change the context of functions bound to a click handler using the &quot;function, context&quot; signature. Unbind the first handler after first click.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  type: "zombie",
  test: function( event ) {
    // Without proxy, `this` would refer to the event target
    // use event.target to reference that element.
    var element = event.target;
    $( element ).css( "background-color", "red" );
​
    // With proxy, `this` refers to the me object encapsulating
    // this function.
    $( "#log" ).append( "Hello " + this.type + "<br>" );
    $( "#test" ).off( "click", this.test );
  }
};
​
var you = {
  type: "person",
  test: function( event ) {
    $( "#log" ).append( this.type + " " );
  }
};
​
// Execute you.test() in the context of the `you` object
// no matter where it is called
// i.e. the `this` keyword will refer to `you`
var youClick = $.proxy( you.test, you );
​
// attach click handlers to #test
$( "#test" )
  // this === "zombie"; handler unbound after first click
  .on( "click", $.proxy( me.test, me ) )
​
  // this === "person"
  .on( "click", youClick )
​
  // this === "zombie"
  .on( "click", $.proxy( you.test, me ) )
​
  // this === "<button> element"
  .on( "click", you.test );
</script>
​
</body>
</html>
```
     * @example ​ ````Change the context of a function bound to the click handler,
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  // I'm a dog
  type: "dog",
​
  // Note that event comes *after* one and two
  test: function( one, two, event ) {
    $( "#log" )
​
      // `one` maps to `you`, the 1st additional
      // argument in the $.proxy function call
      .append( "<h3>Hello " + one.type + ":</h3>" )
​
      // The `this` keyword refers to `me`
      // (the 2nd, context, argument of $.proxy)
      .append( "I am a " + this.type + ", " )
​
      // `two` maps to `they`, the 2nd additional
      // argument in the $.proxy function call
      .append( "and they are " + two.type + ".<br>" )
​
      // The event type is "click"
      .append( "Thanks for " + event.type + "ing." )
​
      // The clicked element is `event.target`,
      // and its type is "button"
      .append( "the " + event.target.type + "." );
  }
};
​
var you = { type: "cat" };
var they = { type: "fish" };
​
// Set up handler to execute me.test() in the context
// of `me`, with `you` and `they` as additional arguments
var proxy = $.proxy( me.test, me, you, they );
​
$( "#test" )
  .on( "click", proxy );
</script>
​
</body>
</html>
```
     */
    proxy<TContext,
        TReturn,
        A,
        T, U, V, W, X>(funсtion: (this: TContext, a: A,
                                  t: T, u: U, v: V, w: W, x: X) => TReturn,
                       context: TContext,
                       a: A): (t: T, u: U, v: V, w: W, x: X) => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.4
     * @since 1.6
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     * @example ​ ````Change the context of functions bound to a click handler using the &quot;function, context&quot; signature. Unbind the first handler after first click.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  type: "zombie",
  test: function( event ) {
    // Without proxy, `this` would refer to the event target
    // use event.target to reference that element.
    var element = event.target;
    $( element ).css( "background-color", "red" );
​
    // With proxy, `this` refers to the me object encapsulating
    // this function.
    $( "#log" ).append( "Hello " + this.type + "<br>" );
    $( "#test" ).off( "click", this.test );
  }
};
​
var you = {
  type: "person",
  test: function( event ) {
    $( "#log" ).append( this.type + " " );
  }
};
​
// Execute you.test() in the context of the `you` object
// no matter where it is called
// i.e. the `this` keyword will refer to `you`
var youClick = $.proxy( you.test, you );
​
// attach click handlers to #test
$( "#test" )
  // this === "zombie"; handler unbound after first click
  .on( "click", $.proxy( me.test, me ) )
​
  // this === "person"
  .on( "click", youClick )
​
  // this === "zombie"
  .on( "click", $.proxy( you.test, me ) )
​
  // this === "<button> element"
  .on( "click", you.test );
</script>
​
</body>
</html>
```
     * @example ​ ````Change the context of a function bound to the click handler,
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  // I'm a dog
  type: "dog",
​
  // Note that event comes *after* one and two
  test: function( one, two, event ) {
    $( "#log" )
​
      // `one` maps to `you`, the 1st additional
      // argument in the $.proxy function call
      .append( "<h3>Hello " + one.type + ":</h3>" )
​
      // The `this` keyword refers to `me`
      // (the 2nd, context, argument of $.proxy)
      .append( "I am a " + this.type + ", " )
​
      // `two` maps to `they`, the 2nd additional
      // argument in the $.proxy function call
      .append( "and they are " + two.type + ".<br>" )
​
      // The event type is "click"
      .append( "Thanks for " + event.type + "ing." )
​
      // The clicked element is `event.target`,
      // and its type is "button"
      .append( "the " + event.target.type + "." );
  }
};
​
var you = { type: "cat" };
var they = { type: "fish" };
​
// Set up handler to execute me.test() in the context
// of `me`, with `you` and `they` as additional arguments
var proxy = $.proxy( me.test, me, you, they );
​
$( "#test" )
  .on( "click", proxy );
</script>
​
</body>
</html>
```
     */
    proxy<TContext,
        TReturn,
        T, U, V, W, X>(funсtion: (this: TContext, t: T, u: U, v: V, w: W, x: X) => TReturn,
                       context: TContext): (t: T, u: U, v: V, w: W, x: X) => TReturn;

    // #endregion

    // region 6 parameters
    // #region 6 parameters

    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @param b An argument to be passed to the function referenced in the `function` argument.
     * @param c An argument to be passed to the function referenced in the `function` argument.
     * @param d An argument to be passed to the function referenced in the `function` argument.
     * @param e An argument to be passed to the function referenced in the `function` argument.
     * @param f An argument to be passed to the function referenced in the `function` argument.
     * @param g An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.4
     * @since 1.6
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     * @example ​ ````Change the context of functions bound to a click handler using the &quot;function, context&quot; signature. Unbind the first handler after first click.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  type: "zombie",
  test: function( event ) {
    // Without proxy, `this` would refer to the event target
    // use event.target to reference that element.
    var element = event.target;
    $( element ).css( "background-color", "red" );
​
    // With proxy, `this` refers to the me object encapsulating
    // this function.
    $( "#log" ).append( "Hello " + this.type + "<br>" );
    $( "#test" ).off( "click", this.test );
  }
};
​
var you = {
  type: "person",
  test: function( event ) {
    $( "#log" ).append( this.type + " " );
  }
};
​
// Execute you.test() in the context of the `you` object
// no matter where it is called
// i.e. the `this` keyword will refer to `you`
var youClick = $.proxy( you.test, you );
​
// attach click handlers to #test
$( "#test" )
  // this === "zombie"; handler unbound after first click
  .on( "click", $.proxy( me.test, me ) )
​
  // this === "person"
  .on( "click", youClick )
​
  // this === "zombie"
  .on( "click", $.proxy( you.test, me ) )
​
  // this === "<button> element"
  .on( "click", you.test );
</script>
​
</body>
</html>
```
     * @example ​ ````Change the context of a function bound to the click handler,
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  // I'm a dog
  type: "dog",
​
  // Note that event comes *after* one and two
  test: function( one, two, event ) {
    $( "#log" )
​
      // `one` maps to `you`, the 1st additional
      // argument in the $.proxy function call
      .append( "<h3>Hello " + one.type + ":</h3>" )
​
      // The `this` keyword refers to `me`
      // (the 2nd, context, argument of $.proxy)
      .append( "I am a " + this.type + ", " )
​
      // `two` maps to `they`, the 2nd additional
      // argument in the $.proxy function call
      .append( "and they are " + two.type + ".<br>" )
​
      // The event type is "click"
      .append( "Thanks for " + event.type + "ing." )
​
      // The clicked element is `event.target`,
      // and its type is "button"
      .append( "the " + event.target.type + "." );
  }
};
​
var you = { type: "cat" };
var they = { type: "fish" };
​
// Set up handler to execute me.test() in the context
// of `me`, with `you` and `they` as additional arguments
var proxy = $.proxy( me.test, me, you, they );
​
$( "#test" )
  .on( "click", proxy );
</script>
​
</body>
</html>
```
     */
    proxy<TContext,
        TReturn,
        A, B, C, D, E, F, G,
        T, U, V, W, X, Y>(funсtion: (this: TContext, a: A, b: B, c: C, d: D, e: E, f: F, g: G,
                                     t: T, u: U, v: V, w: W, x: X, y: Y) => TReturn,
                          context: TContext,
                          a: A, b: B, c: C, d: D, e: E, f: F, g: G): (t: T, u: U, v: V, w: W, x: X, y: Y) => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @param b An argument to be passed to the function referenced in the `function` argument.
     * @param c An argument to be passed to the function referenced in the `function` argument.
     * @param d An argument to be passed to the function referenced in the `function` argument.
     * @param e An argument to be passed to the function referenced in the `function` argument.
     * @param f An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.4
     * @since 1.6
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     * @example ​ ````Change the context of functions bound to a click handler using the &quot;function, context&quot; signature. Unbind the first handler after first click.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  type: "zombie",
  test: function( event ) {
    // Without proxy, `this` would refer to the event target
    // use event.target to reference that element.
    var element = event.target;
    $( element ).css( "background-color", "red" );
​
    // With proxy, `this` refers to the me object encapsulating
    // this function.
    $( "#log" ).append( "Hello " + this.type + "<br>" );
    $( "#test" ).off( "click", this.test );
  }
};
​
var you = {
  type: "person",
  test: function( event ) {
    $( "#log" ).append( this.type + " " );
  }
};
​
// Execute you.test() in the context of the `you` object
// no matter where it is called
// i.e. the `this` keyword will refer to `you`
var youClick = $.proxy( you.test, you );
​
// attach click handlers to #test
$( "#test" )
  // this === "zombie"; handler unbound after first click
  .on( "click", $.proxy( me.test, me ) )
​
  // this === "person"
  .on( "click", youClick )
​
  // this === "zombie"
  .on( "click", $.proxy( you.test, me ) )
​
  // this === "<button> element"
  .on( "click", you.test );
</script>
​
</body>
</html>
```
     * @example ​ ````Change the context of a function bound to the click handler,
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  // I'm a dog
  type: "dog",
​
  // Note that event comes *after* one and two
  test: function( one, two, event ) {
    $( "#log" )
​
      // `one` maps to `you`, the 1st additional
      // argument in the $.proxy function call
      .append( "<h3>Hello " + one.type + ":</h3>" )
​
      // The `this` keyword refers to `me`
      // (the 2nd, context, argument of $.proxy)
      .append( "I am a " + this.type + ", " )
​
      // `two` maps to `they`, the 2nd additional
      // argument in the $.proxy function call
      .append( "and they are " + two.type + ".<br>" )
​
      // The event type is "click"
      .append( "Thanks for " + event.type + "ing." )
​
      // The clicked element is `event.target`,
      // and its type is "button"
      .append( "the " + event.target.type + "." );
  }
};
​
var you = { type: "cat" };
var they = { type: "fish" };
​
// Set up handler to execute me.test() in the context
// of `me`, with `you` and `they` as additional arguments
var proxy = $.proxy( me.test, me, you, they );
​
$( "#test" )
  .on( "click", proxy );
</script>
​
</body>
</html>
```
     */
    proxy<TContext,
        TReturn,
        A, B, C, D, E, F,
        T, U, V, W, X, Y>(funсtion: (this: TContext, a: A, b: B, c: C, d: D, e: E, f: F,
                                     t: T, u: U, v: V, w: W, x: X, y: Y) => TReturn,
                          context: TContext,
                          a: A, b: B, c: C, d: D, e: E, f: F): (t: T, u: U, v: V, w: W, x: X, y: Y) => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @param b An argument to be passed to the function referenced in the `function` argument.
     * @param c An argument to be passed to the function referenced in the `function` argument.
     * @param d An argument to be passed to the function referenced in the `function` argument.
     * @param e An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.4
     * @since 1.6
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     * @example ​ ````Change the context of functions bound to a click handler using the &quot;function, context&quot; signature. Unbind the first handler after first click.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  type: "zombie",
  test: function( event ) {
    // Without proxy, `this` would refer to the event target
    // use event.target to reference that element.
    var element = event.target;
    $( element ).css( "background-color", "red" );
​
    // With proxy, `this` refers to the me object encapsulating
    // this function.
    $( "#log" ).append( "Hello " + this.type + "<br>" );
    $( "#test" ).off( "click", this.test );
  }
};
​
var you = {
  type: "person",
  test: function( event ) {
    $( "#log" ).append( this.type + " " );
  }
};
​
// Execute you.test() in the context of the `you` object
// no matter where it is called
// i.e. the `this` keyword will refer to `you`
var youClick = $.proxy( you.test, you );
​
// attach click handlers to #test
$( "#test" )
  // this === "zombie"; handler unbound after first click
  .on( "click", $.proxy( me.test, me ) )
​
  // this === "person"
  .on( "click", youClick )
​
  // this === "zombie"
  .on( "click", $.proxy( you.test, me ) )
​
  // this === "<button> element"
  .on( "click", you.test );
</script>
​
</body>
</html>
```
     * @example ​ ````Change the context of a function bound to the click handler,
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  // I'm a dog
  type: "dog",
​
  // Note that event comes *after* one and two
  test: function( one, two, event ) {
    $( "#log" )
​
      // `one` maps to `you`, the 1st additional
      // argument in the $.proxy function call
      .append( "<h3>Hello " + one.type + ":</h3>" )
​
      // The `this` keyword refers to `me`
      // (the 2nd, context, argument of $.proxy)
      .append( "I am a " + this.type + ", " )
​
      // `two` maps to `they`, the 2nd additional
      // argument in the $.proxy function call
      .append( "and they are " + two.type + ".<br>" )
​
      // The event type is "click"
      .append( "Thanks for " + event.type + "ing." )
​
      // The clicked element is `event.target`,
      // and its type is "button"
      .append( "the " + event.target.type + "." );
  }
};
​
var you = { type: "cat" };
var they = { type: "fish" };
​
// Set up handler to execute me.test() in the context
// of `me`, with `you` and `they` as additional arguments
var proxy = $.proxy( me.test, me, you, they );
​
$( "#test" )
  .on( "click", proxy );
</script>
​
</body>
</html>
```
     */
    proxy<TContext,
        TReturn,
        A, B, C, D, E,
        T, U, V, W, X, Y>(funсtion: (this: TContext, a: A, b: B, c: C, d: D, e: E,
                                     t: T, u: U, v: V, w: W, x: X, y: Y) => TReturn,
                          context: TContext,
                          a: A, b: B, c: C, d: D, e: E): (t: T, u: U, v: V, w: W, x: X, y: Y) => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @param b An argument to be passed to the function referenced in the `function` argument.
     * @param c An argument to be passed to the function referenced in the `function` argument.
     * @param d An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.4
     * @since 1.6
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     * @example ​ ````Change the context of functions bound to a click handler using the &quot;function, context&quot; signature. Unbind the first handler after first click.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  type: "zombie",
  test: function( event ) {
    // Without proxy, `this` would refer to the event target
    // use event.target to reference that element.
    var element = event.target;
    $( element ).css( "background-color", "red" );
​
    // With proxy, `this` refers to the me object encapsulating
    // this function.
    $( "#log" ).append( "Hello " + this.type + "<br>" );
    $( "#test" ).off( "click", this.test );
  }
};
​
var you = {
  type: "person",
  test: function( event ) {
    $( "#log" ).append( this.type + " " );
  }
};
​
// Execute you.test() in the context of the `you` object
// no matter where it is called
// i.e. the `this` keyword will refer to `you`
var youClick = $.proxy( you.test, you );
​
// attach click handlers to #test
$( "#test" )
  // this === "zombie"; handler unbound after first click
  .on( "click", $.proxy( me.test, me ) )
​
  // this === "person"
  .on( "click", youClick )
​
  // this === "zombie"
  .on( "click", $.proxy( you.test, me ) )
​
  // this === "<button> element"
  .on( "click", you.test );
</script>
​
</body>
</html>
```
     * @example ​ ````Change the context of a function bound to the click handler,
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  // I'm a dog
  type: "dog",
​
  // Note that event comes *after* one and two
  test: function( one, two, event ) {
    $( "#log" )
​
      // `one` maps to `you`, the 1st additional
      // argument in the $.proxy function call
      .append( "<h3>Hello " + one.type + ":</h3>" )
​
      // The `this` keyword refers to `me`
      // (the 2nd, context, argument of $.proxy)
      .append( "I am a " + this.type + ", " )
​
      // `two` maps to `they`, the 2nd additional
      // argument in the $.proxy function call
      .append( "and they are " + two.type + ".<br>" )
​
      // The event type is "click"
      .append( "Thanks for " + event.type + "ing." )
​
      // The clicked element is `event.target`,
      // and its type is "button"
      .append( "the " + event.target.type + "." );
  }
};
​
var you = { type: "cat" };
var they = { type: "fish" };
​
// Set up handler to execute me.test() in the context
// of `me`, with `you` and `they` as additional arguments
var proxy = $.proxy( me.test, me, you, they );
​
$( "#test" )
  .on( "click", proxy );
</script>
​
</body>
</html>
```
     */
    proxy<TContext,
        TReturn,
        A, B, C, D,
        T, U, V, W, X, Y>(funсtion: (this: TContext, a: A, b: B, c: C, d: D,
                                     t: T, u: U, v: V, w: W, x: X, y: Y) => TReturn,
                          context: TContext,
                          a: A, b: B, c: C, d: D): (t: T, u: U, v: V, w: W, x: X, y: Y) => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @param b An argument to be passed to the function referenced in the `function` argument.
     * @param c An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.4
     * @since 1.6
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     * @example ​ ````Change the context of functions bound to a click handler using the &quot;function, context&quot; signature. Unbind the first handler after first click.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  type: "zombie",
  test: function( event ) {
    // Without proxy, `this` would refer to the event target
    // use event.target to reference that element.
    var element = event.target;
    $( element ).css( "background-color", "red" );
​
    // With proxy, `this` refers to the me object encapsulating
    // this function.
    $( "#log" ).append( "Hello " + this.type + "<br>" );
    $( "#test" ).off( "click", this.test );
  }
};
​
var you = {
  type: "person",
  test: function( event ) {
    $( "#log" ).append( this.type + " " );
  }
};
​
// Execute you.test() in the context of the `you` object
// no matter where it is called
// i.e. the `this` keyword will refer to `you`
var youClick = $.proxy( you.test, you );
​
// attach click handlers to #test
$( "#test" )
  // this === "zombie"; handler unbound after first click
  .on( "click", $.proxy( me.test, me ) )
​
  // this === "person"
  .on( "click", youClick )
​
  // this === "zombie"
  .on( "click", $.proxy( you.test, me ) )
​
  // this === "<button> element"
  .on( "click", you.test );
</script>
​
</body>
</html>
```
     * @example ​ ````Change the context of a function bound to the click handler,
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  // I'm a dog
  type: "dog",
​
  // Note that event comes *after* one and two
  test: function( one, two, event ) {
    $( "#log" )
​
      // `one` maps to `you`, the 1st additional
      // argument in the $.proxy function call
      .append( "<h3>Hello " + one.type + ":</h3>" )
​
      // The `this` keyword refers to `me`
      // (the 2nd, context, argument of $.proxy)
      .append( "I am a " + this.type + ", " )
​
      // `two` maps to `they`, the 2nd additional
      // argument in the $.proxy function call
      .append( "and they are " + two.type + ".<br>" )
​
      // The event type is "click"
      .append( "Thanks for " + event.type + "ing." )
​
      // The clicked element is `event.target`,
      // and its type is "button"
      .append( "the " + event.target.type + "." );
  }
};
​
var you = { type: "cat" };
var they = { type: "fish" };
​
// Set up handler to execute me.test() in the context
// of `me`, with `you` and `they` as additional arguments
var proxy = $.proxy( me.test, me, you, they );
​
$( "#test" )
  .on( "click", proxy );
</script>
​
</body>
</html>
```
     */
    proxy<TContext,
        TReturn,
        A, B, C,
        T, U, V, W, X, Y>(funсtion: (this: TContext, a: A, b: B, c: C,
                                     t: T, u: U, v: V, w: W, x: X, y: Y) => TReturn,
                          context: TContext,
                          a: A, b: B, c: C): (t: T, u: U, v: V, w: W, x: X, y: Y) => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @param b An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.4
     * @since 1.6
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     * @example ​ ````Change the context of functions bound to a click handler using the &quot;function, context&quot; signature. Unbind the first handler after first click.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  type: "zombie",
  test: function( event ) {
    // Without proxy, `this` would refer to the event target
    // use event.target to reference that element.
    var element = event.target;
    $( element ).css( "background-color", "red" );
​
    // With proxy, `this` refers to the me object encapsulating
    // this function.
    $( "#log" ).append( "Hello " + this.type + "<br>" );
    $( "#test" ).off( "click", this.test );
  }
};
​
var you = {
  type: "person",
  test: function( event ) {
    $( "#log" ).append( this.type + " " );
  }
};
​
// Execute you.test() in the context of the `you` object
// no matter where it is called
// i.e. the `this` keyword will refer to `you`
var youClick = $.proxy( you.test, you );
​
// attach click handlers to #test
$( "#test" )
  // this === "zombie"; handler unbound after first click
  .on( "click", $.proxy( me.test, me ) )
​
  // this === "person"
  .on( "click", youClick )
​
  // this === "zombie"
  .on( "click", $.proxy( you.test, me ) )
​
  // this === "<button> element"
  .on( "click", you.test );
</script>
​
</body>
</html>
```
     * @example ​ ````Change the context of a function bound to the click handler,
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  // I'm a dog
  type: "dog",
​
  // Note that event comes *after* one and two
  test: function( one, two, event ) {
    $( "#log" )
​
      // `one` maps to `you`, the 1st additional
      // argument in the $.proxy function call
      .append( "<h3>Hello " + one.type + ":</h3>" )
​
      // The `this` keyword refers to `me`
      // (the 2nd, context, argument of $.proxy)
      .append( "I am a " + this.type + ", " )
​
      // `two` maps to `they`, the 2nd additional
      // argument in the $.proxy function call
      .append( "and they are " + two.type + ".<br>" )
​
      // The event type is "click"
      .append( "Thanks for " + event.type + "ing." )
​
      // The clicked element is `event.target`,
      // and its type is "button"
      .append( "the " + event.target.type + "." );
  }
};
​
var you = { type: "cat" };
var they = { type: "fish" };
​
// Set up handler to execute me.test() in the context
// of `me`, with `you` and `they` as additional arguments
var proxy = $.proxy( me.test, me, you, they );
​
$( "#test" )
  .on( "click", proxy );
</script>
​
</body>
</html>
```
     */
    proxy<TContext,
        TReturn,
        A, B,
        T, U, V, W, X, Y>(funсtion: (this: TContext, a: A, b: B,
                                     t: T, u: U, v: V, w: W, x: X, y: Y) => TReturn,
                          context: TContext,
                          a: A, b: B): (t: T, u: U, v: V, w: W, x: X, y: Y) => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.4
     * @since 1.6
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     * @example ​ ````Change the context of functions bound to a click handler using the &quot;function, context&quot; signature. Unbind the first handler after first click.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  type: "zombie",
  test: function( event ) {
    // Without proxy, `this` would refer to the event target
    // use event.target to reference that element.
    var element = event.target;
    $( element ).css( "background-color", "red" );
​
    // With proxy, `this` refers to the me object encapsulating
    // this function.
    $( "#log" ).append( "Hello " + this.type + "<br>" );
    $( "#test" ).off( "click", this.test );
  }
};
​
var you = {
  type: "person",
  test: function( event ) {
    $( "#log" ).append( this.type + " " );
  }
};
​
// Execute you.test() in the context of the `you` object
// no matter where it is called
// i.e. the `this` keyword will refer to `you`
var youClick = $.proxy( you.test, you );
​
// attach click handlers to #test
$( "#test" )
  // this === "zombie"; handler unbound after first click
  .on( "click", $.proxy( me.test, me ) )
​
  // this === "person"
  .on( "click", youClick )
​
  // this === "zombie"
  .on( "click", $.proxy( you.test, me ) )
​
  // this === "<button> element"
  .on( "click", you.test );
</script>
​
</body>
</html>
```
     * @example ​ ````Change the context of a function bound to the click handler,
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  // I'm a dog
  type: "dog",
​
  // Note that event comes *after* one and two
  test: function( one, two, event ) {
    $( "#log" )
​
      // `one` maps to `you`, the 1st additional
      // argument in the $.proxy function call
      .append( "<h3>Hello " + one.type + ":</h3>" )
​
      // The `this` keyword refers to `me`
      // (the 2nd, context, argument of $.proxy)
      .append( "I am a " + this.type + ", " )
​
      // `two` maps to `they`, the 2nd additional
      // argument in the $.proxy function call
      .append( "and they are " + two.type + ".<br>" )
​
      // The event type is "click"
      .append( "Thanks for " + event.type + "ing." )
​
      // The clicked element is `event.target`,
      // and its type is "button"
      .append( "the " + event.target.type + "." );
  }
};
​
var you = { type: "cat" };
var they = { type: "fish" };
​
// Set up handler to execute me.test() in the context
// of `me`, with `you` and `they` as additional arguments
var proxy = $.proxy( me.test, me, you, they );
​
$( "#test" )
  .on( "click", proxy );
</script>
​
</body>
</html>
```
     */
    proxy<TContext,
        TReturn,
        A,
        T, U, V, W, X, Y>(funсtion: (this: TContext, a: A,
                                     t: T, u: U, v: V, w: W, x: X, y: Y) => TReturn,
                          context: TContext,
                          a: A): (t: T, u: U, v: V, w: W, x: X, y: Y) => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.4
     * @since 1.6
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     * @example ​ ````Change the context of functions bound to a click handler using the &quot;function, context&quot; signature. Unbind the first handler after first click.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  type: "zombie",
  test: function( event ) {
    // Without proxy, `this` would refer to the event target
    // use event.target to reference that element.
    var element = event.target;
    $( element ).css( "background-color", "red" );
​
    // With proxy, `this` refers to the me object encapsulating
    // this function.
    $( "#log" ).append( "Hello " + this.type + "<br>" );
    $( "#test" ).off( "click", this.test );
  }
};
​
var you = {
  type: "person",
  test: function( event ) {
    $( "#log" ).append( this.type + " " );
  }
};
​
// Execute you.test() in the context of the `you` object
// no matter where it is called
// i.e. the `this` keyword will refer to `you`
var youClick = $.proxy( you.test, you );
​
// attach click handlers to #test
$( "#test" )
  // this === "zombie"; handler unbound after first click
  .on( "click", $.proxy( me.test, me ) )
​
  // this === "person"
  .on( "click", youClick )
​
  // this === "zombie"
  .on( "click", $.proxy( you.test, me ) )
​
  // this === "<button> element"
  .on( "click", you.test );
</script>
​
</body>
</html>
```
     * @example ​ ````Change the context of a function bound to the click handler,
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  // I'm a dog
  type: "dog",
​
  // Note that event comes *after* one and two
  test: function( one, two, event ) {
    $( "#log" )
​
      // `one` maps to `you`, the 1st additional
      // argument in the $.proxy function call
      .append( "<h3>Hello " + one.type + ":</h3>" )
​
      // The `this` keyword refers to `me`
      // (the 2nd, context, argument of $.proxy)
      .append( "I am a " + this.type + ", " )
​
      // `two` maps to `they`, the 2nd additional
      // argument in the $.proxy function call
      .append( "and they are " + two.type + ".<br>" )
​
      // The event type is "click"
      .append( "Thanks for " + event.type + "ing." )
​
      // The clicked element is `event.target`,
      // and its type is "button"
      .append( "the " + event.target.type + "." );
  }
};
​
var you = { type: "cat" };
var they = { type: "fish" };
​
// Set up handler to execute me.test() in the context
// of `me`, with `you` and `they` as additional arguments
var proxy = $.proxy( me.test, me, you, they );
​
$( "#test" )
  .on( "click", proxy );
</script>
​
</body>
</html>
```
     */
    proxy<TContext,
        TReturn,
        T, U, V, W, X, Y>(funсtion: (this: TContext, t: T, u: U, v: V, w: W, x: X, y: Y) => TReturn,
                          context: TContext): (t: T, u: U, v: V, w: W, x: X, y: Y) => TReturn;

    // #endregion

    // region 7+ parameters
    // #region 7+ parameters

    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @param b An argument to be passed to the function referenced in the `function` argument.
     * @param c An argument to be passed to the function referenced in the `function` argument.
     * @param d An argument to be passed to the function referenced in the `function` argument.
     * @param e An argument to be passed to the function referenced in the `function` argument.
     * @param f An argument to be passed to the function referenced in the `function` argument.
     * @param g An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.4
     * @since 1.6
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     * @example ​ ````Change the context of functions bound to a click handler using the &quot;function, context&quot; signature. Unbind the first handler after first click.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  type: "zombie",
  test: function( event ) {
    // Without proxy, `this` would refer to the event target
    // use event.target to reference that element.
    var element = event.target;
    $( element ).css( "background-color", "red" );
​
    // With proxy, `this` refers to the me object encapsulating
    // this function.
    $( "#log" ).append( "Hello " + this.type + "<br>" );
    $( "#test" ).off( "click", this.test );
  }
};
​
var you = {
  type: "person",
  test: function( event ) {
    $( "#log" ).append( this.type + " " );
  }
};
​
// Execute you.test() in the context of the `you` object
// no matter where it is called
// i.e. the `this` keyword will refer to `you`
var youClick = $.proxy( you.test, you );
​
// attach click handlers to #test
$( "#test" )
  // this === "zombie"; handler unbound after first click
  .on( "click", $.proxy( me.test, me ) )
​
  // this === "person"
  .on( "click", youClick )
​
  // this === "zombie"
  .on( "click", $.proxy( you.test, me ) )
​
  // this === "<button> element"
  .on( "click", you.test );
</script>
​
</body>
</html>
```
     * @example ​ ````Change the context of a function bound to the click handler,
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  // I'm a dog
  type: "dog",
​
  // Note that event comes *after* one and two
  test: function( one, two, event ) {
    $( "#log" )
​
      // `one` maps to `you`, the 1st additional
      // argument in the $.proxy function call
      .append( "<h3>Hello " + one.type + ":</h3>" )
​
      // The `this` keyword refers to `me`
      // (the 2nd, context, argument of $.proxy)
      .append( "I am a " + this.type + ", " )
​
      // `two` maps to `they`, the 2nd additional
      // argument in the $.proxy function call
      .append( "and they are " + two.type + ".<br>" )
​
      // The event type is "click"
      .append( "Thanks for " + event.type + "ing." )
​
      // The clicked element is `event.target`,
      // and its type is "button"
      .append( "the " + event.target.type + "." );
  }
};
​
var you = { type: "cat" };
var they = { type: "fish" };
​
// Set up handler to execute me.test() in the context
// of `me`, with `you` and `they` as additional arguments
var proxy = $.proxy( me.test, me, you, they );
​
$( "#test" )
  .on( "click", proxy );
</script>
​
</body>
</html>
```
     */
    proxy<TContext,
        TReturn,
        A, B, C, D, E, F, G,
        T, U, V, W, X, Y, Z>(funсtion: (this: TContext, a: A, b: B, c: C, d: D, e: E, f: F, g: G,
                                        t: T, u: U, v: V, w: W, x: X, y: Y, z: Z, ...args: any[]) => TReturn,
                             context: TContext,
                             a: A, b: B, c: C, d: D, e: E, f: F, g: G): (t: T, u: U, v: V, w: W, x: X, y: Y, z: Z, ...args: any[]) => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @param b An argument to be passed to the function referenced in the `function` argument.
     * @param c An argument to be passed to the function referenced in the `function` argument.
     * @param d An argument to be passed to the function referenced in the `function` argument.
     * @param e An argument to be passed to the function referenced in the `function` argument.
     * @param f An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.4
     * @since 1.6
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     * @example ​ ````Change the context of functions bound to a click handler using the &quot;function, context&quot; signature. Unbind the first handler after first click.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  type: "zombie",
  test: function( event ) {
    // Without proxy, `this` would refer to the event target
    // use event.target to reference that element.
    var element = event.target;
    $( element ).css( "background-color", "red" );
​
    // With proxy, `this` refers to the me object encapsulating
    // this function.
    $( "#log" ).append( "Hello " + this.type + "<br>" );
    $( "#test" ).off( "click", this.test );
  }
};
​
var you = {
  type: "person",
  test: function( event ) {
    $( "#log" ).append( this.type + " " );
  }
};
​
// Execute you.test() in the context of the `you` object
// no matter where it is called
// i.e. the `this` keyword will refer to `you`
var youClick = $.proxy( you.test, you );
​
// attach click handlers to #test
$( "#test" )
  // this === "zombie"; handler unbound after first click
  .on( "click", $.proxy( me.test, me ) )
​
  // this === "person"
  .on( "click", youClick )
​
  // this === "zombie"
  .on( "click", $.proxy( you.test, me ) )
​
  // this === "<button> element"
  .on( "click", you.test );
</script>
​
</body>
</html>
```
     * @example ​ ````Change the context of a function bound to the click handler,
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  // I'm a dog
  type: "dog",
​
  // Note that event comes *after* one and two
  test: function( one, two, event ) {
    $( "#log" )
​
      // `one` maps to `you`, the 1st additional
      // argument in the $.proxy function call
      .append( "<h3>Hello " + one.type + ":</h3>" )
​
      // The `this` keyword refers to `me`
      // (the 2nd, context, argument of $.proxy)
      .append( "I am a " + this.type + ", " )
​
      // `two` maps to `they`, the 2nd additional
      // argument in the $.proxy function call
      .append( "and they are " + two.type + ".<br>" )
​
      // The event type is "click"
      .append( "Thanks for " + event.type + "ing." )
​
      // The clicked element is `event.target`,
      // and its type is "button"
      .append( "the " + event.target.type + "." );
  }
};
​
var you = { type: "cat" };
var they = { type: "fish" };
​
// Set up handler to execute me.test() in the context
// of `me`, with `you` and `they` as additional arguments
var proxy = $.proxy( me.test, me, you, they );
​
$( "#test" )
  .on( "click", proxy );
</script>
​
</body>
</html>
```
     */
    proxy<TContext,
        TReturn,
        A, B, C, D, E, F,
        T, U, V, W, X, Y, Z>(funсtion: (this: TContext, a: A, b: B, c: C, d: D, e: E, f: F,
                                        t: T, u: U, v: V, w: W, x: X, y: Y, z: Z, ...args: any[]) => TReturn,
                             context: TContext,
                             a: A, b: B, c: C, d: D, e: E, f: F): (t: T, u: U, v: V, w: W, x: X, y: Y, z: Z, ...args: any[]) => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @param b An argument to be passed to the function referenced in the `function` argument.
     * @param c An argument to be passed to the function referenced in the `function` argument.
     * @param d An argument to be passed to the function referenced in the `function` argument.
     * @param e An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.4
     * @since 1.6
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     * @example ​ ````Change the context of functions bound to a click handler using the &quot;function, context&quot; signature. Unbind the first handler after first click.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  type: "zombie",
  test: function( event ) {
    // Without proxy, `this` would refer to the event target
    // use event.target to reference that element.
    var element = event.target;
    $( element ).css( "background-color", "red" );
​
    // With proxy, `this` refers to the me object encapsulating
    // this function.
    $( "#log" ).append( "Hello " + this.type + "<br>" );
    $( "#test" ).off( "click", this.test );
  }
};
​
var you = {
  type: "person",
  test: function( event ) {
    $( "#log" ).append( this.type + " " );
  }
};
​
// Execute you.test() in the context of the `you` object
// no matter where it is called
// i.e. the `this` keyword will refer to `you`
var youClick = $.proxy( you.test, you );
​
// attach click handlers to #test
$( "#test" )
  // this === "zombie"; handler unbound after first click
  .on( "click", $.proxy( me.test, me ) )
​
  // this === "person"
  .on( "click", youClick )
​
  // this === "zombie"
  .on( "click", $.proxy( you.test, me ) )
​
  // this === "<button> element"
  .on( "click", you.test );
</script>
​
</body>
</html>
```
     * @example ​ ````Change the context of a function bound to the click handler,
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  // I'm a dog
  type: "dog",
​
  // Note that event comes *after* one and two
  test: function( one, two, event ) {
    $( "#log" )
​
      // `one` maps to `you`, the 1st additional
      // argument in the $.proxy function call
      .append( "<h3>Hello " + one.type + ":</h3>" )
​
      // The `this` keyword refers to `me`
      // (the 2nd, context, argument of $.proxy)
      .append( "I am a " + this.type + ", " )
​
      // `two` maps to `they`, the 2nd additional
      // argument in the $.proxy function call
      .append( "and they are " + two.type + ".<br>" )
​
      // The event type is "click"
      .append( "Thanks for " + event.type + "ing." )
​
      // The clicked element is `event.target`,
      // and its type is "button"
      .append( "the " + event.target.type + "." );
  }
};
​
var you = { type: "cat" };
var they = { type: "fish" };
​
// Set up handler to execute me.test() in the context
// of `me`, with `you` and `they` as additional arguments
var proxy = $.proxy( me.test, me, you, they );
​
$( "#test" )
  .on( "click", proxy );
</script>
​
</body>
</html>
```
     */
    proxy<TContext,
        TReturn,
        A, B, C, D, E,
        T, U, V, W, X, Y, Z>(funсtion: (this: TContext, a: A, b: B, c: C, d: D, e: E,
                                        t: T, u: U, v: V, w: W, x: X, y: Y, z: Z, ...args: any[]) => TReturn,
                             context: TContext,
                             a: A, b: B, c: C, d: D, e: E): (t: T, u: U, v: V, w: W, x: X, y: Y, z: Z, ...args: any[]) => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @param b An argument to be passed to the function referenced in the `function` argument.
     * @param c An argument to be passed to the function referenced in the `function` argument.
     * @param d An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.4
     * @since 1.6
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     * @example ​ ````Change the context of functions bound to a click handler using the &quot;function, context&quot; signature. Unbind the first handler after first click.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  type: "zombie",
  test: function( event ) {
    // Without proxy, `this` would refer to the event target
    // use event.target to reference that element.
    var element = event.target;
    $( element ).css( "background-color", "red" );
​
    // With proxy, `this` refers to the me object encapsulating
    // this function.
    $( "#log" ).append( "Hello " + this.type + "<br>" );
    $( "#test" ).off( "click", this.test );
  }
};
​
var you = {
  type: "person",
  test: function( event ) {
    $( "#log" ).append( this.type + " " );
  }
};
​
// Execute you.test() in the context of the `you` object
// no matter where it is called
// i.e. the `this` keyword will refer to `you`
var youClick = $.proxy( you.test, you );
​
// attach click handlers to #test
$( "#test" )
  // this === "zombie"; handler unbound after first click
  .on( "click", $.proxy( me.test, me ) )
​
  // this === "person"
  .on( "click", youClick )
​
  // this === "zombie"
  .on( "click", $.proxy( you.test, me ) )
​
  // this === "<button> element"
  .on( "click", you.test );
</script>
​
</body>
</html>
```
     * @example ​ ````Change the context of a function bound to the click handler,
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  // I'm a dog
  type: "dog",
​
  // Note that event comes *after* one and two
  test: function( one, two, event ) {
    $( "#log" )
​
      // `one` maps to `you`, the 1st additional
      // argument in the $.proxy function call
      .append( "<h3>Hello " + one.type + ":</h3>" )
​
      // The `this` keyword refers to `me`
      // (the 2nd, context, argument of $.proxy)
      .append( "I am a " + this.type + ", " )
​
      // `two` maps to `they`, the 2nd additional
      // argument in the $.proxy function call
      .append( "and they are " + two.type + ".<br>" )
​
      // The event type is "click"
      .append( "Thanks for " + event.type + "ing." )
​
      // The clicked element is `event.target`,
      // and its type is "button"
      .append( "the " + event.target.type + "." );
  }
};
​
var you = { type: "cat" };
var they = { type: "fish" };
​
// Set up handler to execute me.test() in the context
// of `me`, with `you` and `they` as additional arguments
var proxy = $.proxy( me.test, me, you, they );
​
$( "#test" )
  .on( "click", proxy );
</script>
​
</body>
</html>
```
     */
    proxy<TContext,
        TReturn,
        A, B, C, D,
        T, U, V, W, X, Y, Z>(funсtion: (this: TContext, a: A, b: B, c: C, d: D,
                                        t: T, u: U, v: V, w: W, x: X, y: Y, z: Z, ...args: any[]) => TReturn,
                             context: TContext,
                             a: A, b: B, c: C, d: D): (t: T, u: U, v: V, w: W, x: X, y: Y, z: Z, ...args: any[]) => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @param b An argument to be passed to the function referenced in the `function` argument.
     * @param c An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.4
     * @since 1.6
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     * @example ​ ````Change the context of functions bound to a click handler using the &quot;function, context&quot; signature. Unbind the first handler after first click.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  type: "zombie",
  test: function( event ) {
    // Without proxy, `this` would refer to the event target
    // use event.target to reference that element.
    var element = event.target;
    $( element ).css( "background-color", "red" );
​
    // With proxy, `this` refers to the me object encapsulating
    // this function.
    $( "#log" ).append( "Hello " + this.type + "<br>" );
    $( "#test" ).off( "click", this.test );
  }
};
​
var you = {
  type: "person",
  test: function( event ) {
    $( "#log" ).append( this.type + " " );
  }
};
​
// Execute you.test() in the context of the `you` object
// no matter where it is called
// i.e. the `this` keyword will refer to `you`
var youClick = $.proxy( you.test, you );
​
// attach click handlers to #test
$( "#test" )
  // this === "zombie"; handler unbound after first click
  .on( "click", $.proxy( me.test, me ) )
​
  // this === "person"
  .on( "click", youClick )
​
  // this === "zombie"
  .on( "click", $.proxy( you.test, me ) )
​
  // this === "<button> element"
  .on( "click", you.test );
</script>
​
</body>
</html>
```
     * @example ​ ````Change the context of a function bound to the click handler,
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  // I'm a dog
  type: "dog",
​
  // Note that event comes *after* one and two
  test: function( one, two, event ) {
    $( "#log" )
​
      // `one` maps to `you`, the 1st additional
      // argument in the $.proxy function call
      .append( "<h3>Hello " + one.type + ":</h3>" )
​
      // The `this` keyword refers to `me`
      // (the 2nd, context, argument of $.proxy)
      .append( "I am a " + this.type + ", " )
​
      // `two` maps to `they`, the 2nd additional
      // argument in the $.proxy function call
      .append( "and they are " + two.type + ".<br>" )
​
      // The event type is "click"
      .append( "Thanks for " + event.type + "ing." )
​
      // The clicked element is `event.target`,
      // and its type is "button"
      .append( "the " + event.target.type + "." );
  }
};
​
var you = { type: "cat" };
var they = { type: "fish" };
​
// Set up handler to execute me.test() in the context
// of `me`, with `you` and `they` as additional arguments
var proxy = $.proxy( me.test, me, you, they );
​
$( "#test" )
  .on( "click", proxy );
</script>
​
</body>
</html>
```
     */
    proxy<TContext,
        TReturn,
        A, B, C,
        T, U, V, W, X, Y, Z>(funсtion: (this: TContext, a: A, b: B, c: C,
                                        t: T, u: U, v: V, w: W, x: X, y: Y, z: Z, ...args: any[]) => TReturn,
                             context: TContext,
                             a: A, b: B, c: C): (t: T, u: U, v: V, w: W, x: X, y: Y, z: Z, ...args: any[]) => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @param b An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.4
     * @since 1.6
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     * @example ​ ````Change the context of functions bound to a click handler using the &quot;function, context&quot; signature. Unbind the first handler after first click.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  type: "zombie",
  test: function( event ) {
    // Without proxy, `this` would refer to the event target
    // use event.target to reference that element.
    var element = event.target;
    $( element ).css( "background-color", "red" );
​
    // With proxy, `this` refers to the me object encapsulating
    // this function.
    $( "#log" ).append( "Hello " + this.type + "<br>" );
    $( "#test" ).off( "click", this.test );
  }
};
​
var you = {
  type: "person",
  test: function( event ) {
    $( "#log" ).append( this.type + " " );
  }
};
​
// Execute you.test() in the context of the `you` object
// no matter where it is called
// i.e. the `this` keyword will refer to `you`
var youClick = $.proxy( you.test, you );
​
// attach click handlers to #test
$( "#test" )
  // this === "zombie"; handler unbound after first click
  .on( "click", $.proxy( me.test, me ) )
​
  // this === "person"
  .on( "click", youClick )
​
  // this === "zombie"
  .on( "click", $.proxy( you.test, me ) )
​
  // this === "<button> element"
  .on( "click", you.test );
</script>
​
</body>
</html>
```
     * @example ​ ````Change the context of a function bound to the click handler,
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  // I'm a dog
  type: "dog",
​
  // Note that event comes *after* one and two
  test: function( one, two, event ) {
    $( "#log" )
​
      // `one` maps to `you`, the 1st additional
      // argument in the $.proxy function call
      .append( "<h3>Hello " + one.type + ":</h3>" )
​
      // The `this` keyword refers to `me`
      // (the 2nd, context, argument of $.proxy)
      .append( "I am a " + this.type + ", " )
​
      // `two` maps to `they`, the 2nd additional
      // argument in the $.proxy function call
      .append( "and they are " + two.type + ".<br>" )
​
      // The event type is "click"
      .append( "Thanks for " + event.type + "ing." )
​
      // The clicked element is `event.target`,
      // and its type is "button"
      .append( "the " + event.target.type + "." );
  }
};
​
var you = { type: "cat" };
var they = { type: "fish" };
​
// Set up handler to execute me.test() in the context
// of `me`, with `you` and `they` as additional arguments
var proxy = $.proxy( me.test, me, you, they );
​
$( "#test" )
  .on( "click", proxy );
</script>
​
</body>
</html>
```
     */
    proxy<TContext,
        TReturn,
        A, B,
        T, U, V, W, X, Y, Z>(funсtion: (this: TContext, a: A, b: B,
                                        t: T, u: U, v: V, w: W, x: X, y: Y, z: Z, ...args: any[]) => TReturn,
                             context: TContext,
                             a: A, b: B): (t: T, u: U, v: V, w: W, x: X, y: Y, z: Z, ...args: any[]) => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param a An argument to be passed to the function referenced in the `function` argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.4
     * @since 1.6
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     * @example ​ ````Change the context of functions bound to a click handler using the &quot;function, context&quot; signature. Unbind the first handler after first click.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  type: "zombie",
  test: function( event ) {
    // Without proxy, `this` would refer to the event target
    // use event.target to reference that element.
    var element = event.target;
    $( element ).css( "background-color", "red" );
​
    // With proxy, `this` refers to the me object encapsulating
    // this function.
    $( "#log" ).append( "Hello " + this.type + "<br>" );
    $( "#test" ).off( "click", this.test );
  }
};
​
var you = {
  type: "person",
  test: function( event ) {
    $( "#log" ).append( this.type + " " );
  }
};
​
// Execute you.test() in the context of the `you` object
// no matter where it is called
// i.e. the `this` keyword will refer to `you`
var youClick = $.proxy( you.test, you );
​
// attach click handlers to #test
$( "#test" )
  // this === "zombie"; handler unbound after first click
  .on( "click", $.proxy( me.test, me ) )
​
  // this === "person"
  .on( "click", youClick )
​
  // this === "zombie"
  .on( "click", $.proxy( you.test, me ) )
​
  // this === "<button> element"
  .on( "click", you.test );
</script>
​
</body>
</html>
```
     * @example ​ ````Change the context of a function bound to the click handler,
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  // I'm a dog
  type: "dog",
​
  // Note that event comes *after* one and two
  test: function( one, two, event ) {
    $( "#log" )
​
      // `one` maps to `you`, the 1st additional
      // argument in the $.proxy function call
      .append( "<h3>Hello " + one.type + ":</h3>" )
​
      // The `this` keyword refers to `me`
      // (the 2nd, context, argument of $.proxy)
      .append( "I am a " + this.type + ", " )
​
      // `two` maps to `they`, the 2nd additional
      // argument in the $.proxy function call
      .append( "and they are " + two.type + ".<br>" )
​
      // The event type is "click"
      .append( "Thanks for " + event.type + "ing." )
​
      // The clicked element is `event.target`,
      // and its type is "button"
      .append( "the " + event.target.type + "." );
  }
};
​
var you = { type: "cat" };
var they = { type: "fish" };
​
// Set up handler to execute me.test() in the context
// of `me`, with `you` and `they` as additional arguments
var proxy = $.proxy( me.test, me, you, they );
​
$( "#test" )
  .on( "click", proxy );
</script>
​
</body>
</html>
```
     */
    proxy<TContext,
        TReturn,
        A,
        T, U, V, W, X, Y, Z>(funсtion: (this: TContext, a: A,
                                        t: T, u: U, v: V, w: W, x: X, y: Y, z: Z, ...args: any[]) => TReturn,
                             context: TContext,
                             a: A): (t: T, u: U, v: V, w: W, x: X, y: Y, z: Z, ...args: any[]) => TReturn;
    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.4
     * @since 1.6
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     * @example ​ ````Change the context of functions bound to a click handler using the &quot;function, context&quot; signature. Unbind the first handler after first click.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  type: "zombie",
  test: function( event ) {
    // Without proxy, `this` would refer to the event target
    // use event.target to reference that element.
    var element = event.target;
    $( element ).css( "background-color", "red" );
​
    // With proxy, `this` refers to the me object encapsulating
    // this function.
    $( "#log" ).append( "Hello " + this.type + "<br>" );
    $( "#test" ).off( "click", this.test );
  }
};
​
var you = {
  type: "person",
  test: function( event ) {
    $( "#log" ).append( this.type + " " );
  }
};
​
// Execute you.test() in the context of the `you` object
// no matter where it is called
// i.e. the `this` keyword will refer to `you`
var youClick = $.proxy( you.test, you );
​
// attach click handlers to #test
$( "#test" )
  // this === "zombie"; handler unbound after first click
  .on( "click", $.proxy( me.test, me ) )
​
  // this === "person"
  .on( "click", youClick )
​
  // this === "zombie"
  .on( "click", $.proxy( you.test, me ) )
​
  // this === "<button> element"
  .on( "click", you.test );
</script>
​
</body>
</html>
```
     * @example ​ ````Change the context of a function bound to the click handler,
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  // I'm a dog
  type: "dog",
​
  // Note that event comes *after* one and two
  test: function( one, two, event ) {
    $( "#log" )
​
      // `one` maps to `you`, the 1st additional
      // argument in the $.proxy function call
      .append( "<h3>Hello " + one.type + ":</h3>" )
​
      // The `this` keyword refers to `me`
      // (the 2nd, context, argument of $.proxy)
      .append( "I am a " + this.type + ", " )
​
      // `two` maps to `they`, the 2nd additional
      // argument in the $.proxy function call
      .append( "and they are " + two.type + ".<br>" )
​
      // The event type is "click"
      .append( "Thanks for " + event.type + "ing." )
​
      // The clicked element is `event.target`,
      // and its type is "button"
      .append( "the " + event.target.type + "." );
  }
};
​
var you = { type: "cat" };
var they = { type: "fish" };
​
// Set up handler to execute me.test() in the context
// of `me`, with `you` and `they` as additional arguments
var proxy = $.proxy( me.test, me, you, they );
​
$( "#test" )
  .on( "click", proxy );
</script>
​
</body>
</html>
```
     */
    proxy<TContext,
        TReturn,
        T, U, V, W, X, Y, Z>(funсtion: (this: TContext, t: T, u: U, v: V, w: W, x: X, y: Y, z: Z, ...args: any[]) => TReturn,
                             context: TContext): (t: T, u: U, v: V, w: W, x: X, y: Y, z: Z, ...args: any[]) => TReturn;

    // #endregion

    // #endregion

    // region 8+ additional arguments
    // #region 8+ additional arguments

    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param funсtion The function whose context will be changed.
     * @param context The object to which the context (`this`) of the function should be set.
     * @param additionalArguments Any number of arguments to be passed to the function referenced in the function argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.4
     * @since 1.6
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     * @example ​ ````Change the context of functions bound to a click handler using the &quot;function, context&quot; signature. Unbind the first handler after first click.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  type: "zombie",
  test: function( event ) {
    // Without proxy, `this` would refer to the event target
    // use event.target to reference that element.
    var element = event.target;
    $( element ).css( "background-color", "red" );
​
    // With proxy, `this` refers to the me object encapsulating
    // this function.
    $( "#log" ).append( "Hello " + this.type + "<br>" );
    $( "#test" ).off( "click", this.test );
  }
};
​
var you = {
  type: "person",
  test: function( event ) {
    $( "#log" ).append( this.type + " " );
  }
};
​
// Execute you.test() in the context of the `you` object
// no matter where it is called
// i.e. the `this` keyword will refer to `you`
var youClick = $.proxy( you.test, you );
​
// attach click handlers to #test
$( "#test" )
  // this === "zombie"; handler unbound after first click
  .on( "click", $.proxy( me.test, me ) )
​
  // this === "person"
  .on( "click", youClick )
​
  // this === "zombie"
  .on( "click", $.proxy( you.test, me ) )
​
  // this === "<button> element"
  .on( "click", you.test );
</script>
​
</body>
</html>
```
     * @example ​ ````Change the context of a function bound to the click handler,
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button type="button" id="test">Test</button></p>
<div id="log"></div>
​
<script>
var me = {
  // I'm a dog
  type: "dog",
​
  // Note that event comes *after* one and two
  test: function( one, two, event ) {
    $( "#log" )
​
      // `one` maps to `you`, the 1st additional
      // argument in the $.proxy function call
      .append( "<h3>Hello " + one.type + ":</h3>" )
​
      // The `this` keyword refers to `me`
      // (the 2nd, context, argument of $.proxy)
      .append( "I am a " + this.type + ", " )
​
      // `two` maps to `they`, the 2nd additional
      // argument in the $.proxy function call
      .append( "and they are " + two.type + ".<br>" )
​
      // The event type is "click"
      .append( "Thanks for " + event.type + "ing." )
​
      // The clicked element is `event.target`,
      // and its type is "button"
      .append( "the " + event.target.type + "." );
  }
};
​
var you = { type: "cat" };
var they = { type: "fish" };
​
// Set up handler to execute me.test() in the context
// of `me`, with `you` and `they` as additional arguments
var proxy = $.proxy( me.test, me, you, they );
​
$( "#test" )
  .on( "click", proxy );
</script>
​
</body>
</html>
```
     */
    proxy<TContext,
        TReturn>(funсtion: (this: TContext, ...args: any[]) => TReturn,
                 context: TContext,
                 ...additionalArguments: any[]): (...args: any[]) => TReturn;

    // #endregion

    // #endregion

    // region (context, name)
    // #region (context, name)

    /**
     * Takes a function and returns a new one that will always have a particular context.
     * @param context The object to which the context of the function should be set.
     * @param name The name of the function whose context will be changed (should be a property of the context object).
     * @param additionalArguments Any number of arguments to be passed to the function named in the name argument.
     * @see \`{@link https://api.jquery.com/jQuery.proxy/ }\`
     * @since 1.4
     * @since 1.6
     * @deprecated ​ Deprecated since 3.3. Use \`{@link Function#bind }\`.
     * @example ​ ````Enforce the context of the function using the &quot;context, function name&quot; signature. Unbind the handler after first click.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.proxy demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
  <p><button id="test">Test</button></p>
  <p id="log"></p>
​
<script>
var obj = {
  name: "John",
  test: function() {
    $( "#log" ).append( this.name );
    $( "#test" ).off( "click", obj.test );
  }
};
$( "#test" ).on( "click", jQuery.proxy( obj, "test" ) );
</script>
​
</body>
</html>
```
     */
    proxy<TContext>(context: TContext,
                    name: keyof TContext,
                    ...additionalArguments: any[]): (...args: any[]) => any;

    // #endregion

    // #endregion

    /**
     * Manipulate the queue of functions to be executed on the matched element.
     * @param element A DOM element where the array of queued functions is attached.
     * @param queueName A string containing the name of the queue. Defaults to fx, the standard effects queue.
     * @param newQueue The new function to add to the queue.
     *                 An array of functions to replace the current queue contents.
     * @see \`{@link https://api.jquery.com/jQuery.queue/ }\`
     * @since 1.3
     * @example ​ ````Show the length of the queue.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.queue demo</title>
  <style>
  div {
    margin: 3px;
    width: 40px;
    height: 40px;
    position: absolute;
    left: 0px;
    top: 30px;
    background: green;
    display: none;
  }
  div.newcolor {
    background: blue;
  }
  span {
    color: red;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<button id="show">Show Length of Queue</button>
<span></span>
<div></div>
  ​
<script>
$( "#show" ).click(function() {
  var n = jQuery.queue( $( "div" )[ 0 ], "fx" );
  $( "span" ).text( "Queue length is: " + n.length );
});
​
function runIt() {
  $( "div" )
    .show( "slow" )
    .animate({
      left: "+=200"
    }, 2000 )
    .slideToggle( 1000 )
    .slideToggle( "fast" )
    .animate({
      left: "-=200"
    }, 1500 )
    .hide( "slow" )
    .show( 1200 )
    .slideUp( "normal", runIt );
}
​
runIt();
</script>
​
</body>
</html>
```
     * @example ​ ````Queue a custom function.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.queue demo</title>
  <style>
  div {
    margin: 3px;
    width: 40px;
    height: 40px;
    position: absolute;
    left: 0px;
    top: 30px;
    background: green;
    display: none;
  }
  div.newcolor {
    background: blue;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
Click here...
<div></div>
​
<script>
$( document.body ).click(function() {
  var divs = $( "div" )
    .show( "slow" )
    .animate({ left: "+=200" }, 2000 );
  jQuery.queue( divs[ 0 ], "fx", function() {
    $( this ).addClass( "newcolor" );
    jQuery.dequeue( this );
  });
  divs.animate({ left: "-=200" }, 500 );
  jQuery.queue( divs[ 0 ], "fx", function() {
    $( this ).removeClass( "newcolor" );
    jQuery.dequeue( this );
  });
  divs.slideUp();
});
</script>
​
</body>
</html>
```
     * @example ​ ````Set a queue array to delete the queue.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.queue demo</title>
  <style>
  div {
    margin: 3px;
    width: 40px;
    height: 40px;
    position: absolute;
    left: 0px;
    top: 30px;
    background: green;
    display: none;
  }
  div.newcolor {
    background: blue;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<button id="start">Start</button>
<button id="stop">Stop</button>
<div></div>
​
<script>
$( "#start" ).click(function() {
  var divs = $( "div" )
    .show( "slow" )
    .animate({ left: "+=200" }, 5000 );
  jQuery.queue( divs[ 0 ], "fx", function() {
    $( this ).addClass( "newcolor" );
    jQuery.dequeue( this );
  });
  divs.animate({ left: "-=200" }, 1500 );
  jQuery.queue( divs[ 0 ], "fx", function() {
    $( this ).removeClass( "newcolor" );
    jQuery.dequeue( this );
  });
  divs.slideUp();
});
$( "#stop" ).click(function() {
  jQuery.queue( $( "div" )[ 0 ], "fx", [] );
  $( "div" ).stop();
});
</script>
​
</body>
</html>
```
     */
    queue<T extends Element>(element: T, queueName?: string, newQueue?: JQuery.TypeOrArray<JQuery.QueueFunction<T>>): JQuery.Queue<T>;
    /**
     * Handles errors thrown synchronously in functions wrapped in jQuery().
     * @param error An error thrown in the function wrapped in jQuery().
     * @see \`{@link https://api.jquery.com/jQuery.readyException/ }\`
     * @since 3.1
     * @example ​ ````Pass the received error to console.error.
```javascript
jQuery.readyException = function( error ) {
  console.error( error );
};
```
     */
    readyException(error: Error): any;
    /**
     * Remove a previously-stored piece of data.
     * @param element A DOM element from which to remove data.
     * @param name A string naming the piece of data to remove.
     * @see \`{@link https://api.jquery.com/jQuery.removeData/ }\`
     * @since 1.2.3
     * @example ​ ````Set a data store for 2 names then remove one of them.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.removeData demo</title>
  <style>
  div {
    margin: 2px;
    color: blue;
  }
  span {
    color: red;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<div>value1 before creation: <span></span></div>
<div>value1 after creation: <span></span></div>
<div>value1 after removal: <span></span></div>
<div>value2 after removal: <span></span></div>
​
<script>
var div = $( "div" )[ 0 ];
$( "span:eq(0)" ).text( "" + $( "div" ).data( "test1" ) );
jQuery.data( div, "test1", "VALUE-1" );
jQuery.data( div, "test2", "VALUE-2" );
$( "span:eq(1)" ).text( "" + jQuery.data( div, "test1" ) );
jQuery.removeData( div, "test1" );
$( "span:eq(2)" ).text( "" + jQuery.data( div, "test1" ) );
$( "span:eq(3)" ).text( "" + jQuery.data( div, "test2" ) );
</script>
​
</body>
</html>
```
     */
    removeData(element: Element | Document | Window | JQuery.PlainObject, name?: string): void;
    /**
     * Creates an object containing a set of properties ready to be used in the definition of custom animations.
     * @param duration A string or number determining how long the animation will run.
     * @param easing A string indicating which easing function to use for the transition.
     * @param complete A function to call once the animation is complete, called once per matched element.
     * @see \`{@link https://api.jquery.com/jQuery.speed/ }\`
     * @since 1.1
     */
    speed<TElement extends Element = HTMLElement>(duration: JQuery.Duration, easing: string, complete: (this: TElement) => void): JQuery.EffectsOptions<TElement>;
    /**
     * Creates an object containing a set of properties ready to be used in the definition of custom animations.
     * @param duration A string or number determining how long the animation will run.
     * @param easing_complete _&#x40;param_ `easing_complete`
     * <br>
     * * `easing` — A string indicating which easing function to use for the transition. <br>
     * * `complete` — A function to call once the animation is complete, called once per matched element.
     * @see \`{@link https://api.jquery.com/jQuery.speed/ }\`
     * @since 1.0
     * @since 1.1
     */
    speed<TElement extends Element = HTMLElement>(duration: JQuery.Duration,
                                                  easing_complete: string | ((this: TElement) => void)): JQuery.EffectsOptions<TElement>;
    /**
     * Creates an object containing a set of properties ready to be used in the definition of custom animations.
     * @param duration_complete_settings _&#x40;param_ `duration_complete_settings`
     * <br>
     * * `duration` — A string or number determining how long the animation will run. <br>
     * * `complete` — A function to call once the animation is complete, called once per matched element. <br>
     * * `settings` —
     * @see \`{@link https://api.jquery.com/jQuery.speed/ }\`
     * @since 1.0
     * @since 1.1
     */
    speed<TElement extends Element = HTMLElement>(duration_complete_settings?: JQuery.Duration | ((this: TElement) => void) | JQuery.SpeedSettings<TElement>): JQuery.EffectsOptions<TElement>;
    /**
     * Remove the whitespace from the beginning and end of a string.
     * @param str The string to trim.
     * @see \`{@link https://api.jquery.com/jQuery.trim/ }\`
     * @since 1.0
     * @example ​ ````Remove the white spaces at the start and at the end of the string.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.trim demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<pre id="original"></pre>
<pre id="trimmed"></pre>
​
<script>
var str = "         lots of spaces before and after         ";
$( "#original" ).html( "Original String: '" + str + "'" );
$( "#trimmed" ).html( "$.trim()'ed: '" + $.trim(str) + "'" );
</script>
​
</body>
</html>
```
     * @example ​ ````Remove the white spaces at the start and at the end of the string.
```javascript
$.trim("    hello, how are you?    ");
```
     * @example ​ ````Remove the white spaces at the start and at the end of the string.
```javascript
$.trim("    hello, how are you?    ");
```
     */
    trim(str: string): string;
    /**
     * Determine the internal JavaScript [[Class]] of an object.
     * @param obj Object to get the internal JavaScript [[Class]] of.
     * @see \`{@link https://api.jquery.com/jQuery.type/ }\`
     * @since 1.4.3
     * @deprecated ​ Deprecated since 3.3. See \`{@link https://github.com/jquery/jquery/issues/3605 }\`.
     * @example ​ ````Find out if the parameter is a RegExp.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.type demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
Is it a RegExp? <b></b>
​
<script>
$( "b" ).append( "" + jQuery.type( /test/ ) );
</script>
​
</body>
</html>
```
     */
    type(obj: any): 'array' | 'boolean' | 'date' | 'error' | 'function' | 'null' | 'number' | 'object' | 'regexp' | 'string' | 'symbol' | 'undefined';
    /**
     * Sorts an array of DOM elements, in place, with the duplicates removed. Note that this only works on arrays of DOM elements, not strings or numbers.
     * @param array The Array of DOM elements.
     * @see \`{@link https://api.jquery.com/jQuery.unique/ }\`
     * @since 1.1.3
     * @deprecated ​ Deprecated since 3.0. Use \`{@link uniqueSort }\`.
     *
     * **Cause**: The fact that `jQuery.unique` sorted its results in DOM order was surprising to many who did not read the documentation carefully. As of jQuery 3.0 this function is being renamed to make it clear.
     *
     * **Solution**: Replace all uses of `jQuery.unique` with `jQuery.uniqueSort` which is the same function with a better name.
     * @example ​ ````Removes any duplicate elements from the array of divs.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.unique demo</title>
  <style>
  div {
    color: blue;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<div>There are 6 divs in this document.</div>
<div></div>
<div class="dup"></div>
<div class="dup"></div>
<div class="dup"></div>
<div></div>
​
<script>
// unique() must take a native array
var divs = $( "div" ).get();
​
// Add 3 elements of class dup too (they are divs)
divs = divs.concat( $( ".dup" ).get() );
$( "div:eq(1)" ).text( "Pre-unique there are " + divs.length + " elements." );
​
divs = jQuery.unique( divs );
$( "div:eq(2)" ).text( "Post-unique there are " + divs.length + " elements." )
  .css( "color", "red" );
</script>
​
</body>
</html>
```
     */
    unique<T extends Element>(array: T[]): T[];
    /**
     * Sorts an array of DOM elements, in place, with the duplicates removed. Note that this only works on arrays of DOM elements, not strings or numbers.
     * @param array The Array of DOM elements.
     * @see \`{@link https://api.jquery.com/jQuery.uniqueSort/ }\`
     * @since 1.12
     * @since 2.2
     * @example ​ ````Removes any duplicate elements from the array of divs.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.uniqueSort demo</title>
  <style>
  div {
    color: blue;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<div>There are 6 divs in this document.</div>
<div></div>
<div class="dup"></div>
<div class="dup"></div>
<div class="dup"></div>
<div></div>
​
<script>
// unique() must take a native array
var divs = $( "div" ).get();
​
// Add 3 elements of class dup too (they are divs)
divs = divs.concat( $( ".dup" ).get() );
$( "div:eq(1)" ).text( "Pre-unique there are " + divs.length + " elements." );
​
divs = jQuery.uniqueSort( divs );
$( "div:eq(2)" ).text( "Post-unique there are " + divs.length + " elements." )
  .css( "color", "red" );
</script>
​
</body>
</html>
```
     */
    uniqueSort<T extends Element>(array: T[]): T[];
    /**
     * Provides a way to execute callback functions based on zero or more Thenable objects, usually Deferred objects that represent asynchronous events.
     * @see \`{@link https://api.jquery.com/jQuery.when/ }\`
     * @since 1.5
     * @example ​ ````Execute a function after two Ajax requests are successful. (See the jQuery.ajax() documentation for a complete description of success and error cases for an ajax request).
```javascript
$.when( $.ajax( "/page1.php" ), $.ajax( "/page2.php" ) ).done(function( a1, a2 ) {
  // a1 and a2 are arguments resolved for the page1 and page2 ajax requests, respectively.
  // Each argument is an array with the following structure: [ data, statusText, jqXHR ]
  var data = a1[ 0 ] + a2[ 0 ]; // a1[ 0 ] = "Whip", a2[ 0 ] = " It"
  if ( /Whip It/.test( data ) ) {
    alert( "We got what we came for!" );
  }
});
```
     * @example ​ ````Execute the function myFunc when both ajax requests are successful, or myFailure if either one has an error.
```javascript
$.when( $.ajax( "/page1.php" ), $.ajax( "/page2.php" ) )
  .then( myFunc, myFailure );
```
     */
    when<TR1, UR1, VR1,
        TJ1 = any, UJ1 = any, VJ1 = any>(
            deferredT: JQuery.Promise<TR1, TJ1> | JQuery.Thenable<TR1> | TR1,
            deferredU: JQuery.Promise<UR1, UJ1> | JQuery.Thenable<UR1> | UR1,
            deferredV: JQuery.Promise<VR1, VJ1> | JQuery.Thenable<VR1> | VR1,
    ): JQuery.Promise3<
        TR1, TJ1, never,
        UR1, UJ1, never,
        VR1, VJ1, never>;
    /**
     * Provides a way to execute callback functions based on zero or more Thenable objects, usually Deferred objects that represent asynchronous events.
     * @see \`{@link https://api.jquery.com/jQuery.when/ }\`
     * @since 1.5
     * @example ​ ````Execute a function after two Ajax requests are successful. (See the jQuery.ajax() documentation for a complete description of success and error cases for an ajax request).
```javascript
$.when( $.ajax( "/page1.php" ), $.ajax( "/page2.php" ) ).done(function( a1, a2 ) {
  // a1 and a2 are arguments resolved for the page1 and page2 ajax requests, respectively.
  // Each argument is an array with the following structure: [ data, statusText, jqXHR ]
  var data = a1[ 0 ] + a2[ 0 ]; // a1[ 0 ] = "Whip", a2[ 0 ] = " It"
  if ( /Whip It/.test( data ) ) {
    alert( "We got what we came for!" );
  }
});
```
     * @example ​ ````Execute the function myFunc when both ajax requests are successful, or myFailure if either one has an error.
```javascript
$.when( $.ajax( "/page1.php" ), $.ajax( "/page2.php" ) )
  .then( myFunc, myFailure );
```
     */
    when<TR1, UR1,
        TJ1 = any, UJ1 = any>(
            deferredT: JQuery.Promise<TR1, TJ1> | JQuery.Thenable<TR1> | TR1,
            deferredU: JQuery.Promise<UR1, UJ1> | JQuery.Thenable<UR1> | UR1,
    ): JQuery.Promise2<
        TR1, TJ1, never,
        UR1, UJ1, never>;
    /**
     * Provides a way to execute callback functions based on zero or more Thenable objects, usually Deferred objects that represent asynchronous events.
     * @see \`{@link https://api.jquery.com/jQuery.when/ }\`
     * @since 1.5
     * @example ​ ````Execute a function after two Ajax requests are successful. (See the jQuery.ajax() documentation for a complete description of success and error cases for an ajax request).
```javascript
$.when( $.ajax( "/page1.php" ), $.ajax( "/page2.php" ) ).done(function( a1, a2 ) {
  // a1 and a2 are arguments resolved for the page1 and page2 ajax requests, respectively.
  // Each argument is an array with the following structure: [ data, statusText, jqXHR ]
  var data = a1[ 0 ] + a2[ 0 ]; // a1[ 0 ] = "Whip", a2[ 0 ] = " It"
  if ( /Whip It/.test( data ) ) {
    alert( "We got what we came for!" );
  }
});
```
     * @example ​ ````Execute the function myFunc when both ajax requests are successful, or myFailure if either one has an error.
```javascript
$.when( $.ajax( "/page1.php" ), $.ajax( "/page2.php" ) )
  .then( myFunc, myFailure );
```
     */
    when<TR1, TJ1,
        TR2, TJ2,
        TR3 = never, TJ3 = never>(
            deferredT: JQuery.Promise3<TR1, TJ1, any, TR2, TJ2, any, TR3, TJ3, any> |
                       JQuery.Promise2<TR1, TJ1, any, TR2, TJ2, any>
    ): JQuery.Promise3<
        TR1, TJ1, never,
        TR2, TJ2, never,
        TR3, TJ3, never>;
    /**
     * Provides a way to execute callback functions based on zero or more Thenable objects, usually Deferred objects that represent asynchronous events.
     * @see \`{@link https://api.jquery.com/jQuery.when/ }\`
     * @since 1.5
     * @example ​ ````Execute a function after two Ajax requests are successful. (See the jQuery.ajax() documentation for a complete description of success and error cases for an ajax request).
```javascript
$.when( $.ajax( "/page1.php" ), $.ajax( "/page2.php" ) ).done(function( a1, a2 ) {
  // a1 and a2 are arguments resolved for the page1 and page2 ajax requests, respectively.
  // Each argument is an array with the following structure: [ data, statusText, jqXHR ]
  var data = a1[ 0 ] + a2[ 0 ]; // a1[ 0 ] = "Whip", a2[ 0 ] = " It"
  if ( /Whip It/.test( data ) ) {
    alert( "We got what we came for!" );
  }
});
```
     * @example ​ ````Execute the function myFunc when both ajax requests are successful, or myFailure if either one has an error.
```javascript
$.when( $.ajax( "/page1.php" ), $.ajax( "/page2.php" ) )
  .then( myFunc, myFailure );
```
     */
    when<TR1, TJ1 = any>(deferred: JQuery.Promise<TR1, TJ1> | JQuery.Thenable<TR1> | TR1): JQuery.Promise<TR1, TJ1, never>;
    /**
     * Provides a way to execute callback functions based on zero or more Thenable objects, usually Deferred objects that represent asynchronous events.
     * @param deferreds Zero or more Thenable objects.
     * @see \`{@link https://api.jquery.com/jQuery.when/ }\`
     * @since 1.5
     * @example ​ ````Execute a function after two Ajax requests are successful. (See the jQuery.ajax() documentation for a complete description of success and error cases for an ajax request).
```javascript
$.when( $.ajax( "/page1.php" ), $.ajax( "/page2.php" ) ).done(function( a1, a2 ) {
  // a1 and a2 are arguments resolved for the page1 and page2 ajax requests, respectively.
  // Each argument is an array with the following structure: [ data, statusText, jqXHR ]
  var data = a1[ 0 ] + a2[ 0 ]; // a1[ 0 ] = "Whip", a2[ 0 ] = " It"
  if ( /Whip It/.test( data ) ) {
    alert( "We got what we came for!" );
  }
});
```
     * @example ​ ````Execute the function myFunc when both ajax requests are successful, or myFailure if either one has an error.
```javascript
$.when( $.ajax( "/page1.php" ), $.ajax( "/page2.php" ) )
  .then( myFunc, myFailure );
```
     */
    when<TR1 = never, TJ1 = never>(...deferreds: Array<JQuery.Promise<TR1, TJ1> | JQuery.Thenable<TR1> | TR1>): JQuery.Promise<TR1, TJ1, never>;
    /**
     * Provides a way to execute callback functions based on zero or more Thenable objects, usually Deferred objects that represent asynchronous events.
     * @param deferreds Zero or more Thenable objects.
     * @see \`{@link https://api.jquery.com/jQuery.when/ }\`
     * @since 1.5
     * @example ​ ````Execute a function after two Ajax requests are successful. (See the jQuery.ajax() documentation for a complete description of success and error cases for an ajax request).
```javascript
$.when( $.ajax( "/page1.php" ), $.ajax( "/page2.php" ) ).done(function( a1, a2 ) {
  // a1 and a2 are arguments resolved for the page1 and page2 ajax requests, respectively.
  // Each argument is an array with the following structure: [ data, statusText, jqXHR ]
  var data = a1[ 0 ] + a2[ 0 ]; // a1[ 0 ] = "Whip", a2[ 0 ] = " It"
  if ( /Whip It/.test( data ) ) {
    alert( "We got what we came for!" );
  }
});
```
     * @example ​ ````Execute the function myFunc when both ajax requests are successful, or myFailure if either one has an error.
```javascript
$.when( $.ajax( "/page1.php" ), $.ajax( "/page2.php" ) )
  .then( myFunc, myFailure );
```
     */
    when(...deferreds: any[]): JQuery.Promise<any, any, never>;
}
