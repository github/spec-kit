// tslint:disable:jsdoc-format
// tslint:disable:max-line-length
// tslint:disable:no-irregular-whitespace

interface JQuery<TElement = HTMLElement> extends Iterable<TElement> {
    /**
     * A string containing the jQuery version number.
     * @see \`{@link https://api.jquery.com/jquery-2/#jquery1 }\`
     * @since 1.0
     * @example ​ ````Determine if an object is a jQuery object
```javascript
var a = { what: "A regular JS object" },
  b = $( "body" );
​
if ( a.jquery ) { // Falsy, since it's undefined
  alert( "a is a jQuery object!" );
}
​
if ( b.jquery ) { // Truthy, since it's a string
    alert( "b is a jQuery object!" );
}
```
     * @example ​ ````Get the current version of jQuery running on the page
```javascript
alert( "You are running jQuery version: " + $.fn.jquery );
```
     */
    jquery: string;
    /**
     * The number of elements in the jQuery object.
     * @see \`{@link https://api.jquery.com/length/ }\`
     * @since 1.0
     * @example ​ ````Count the divs.  Click to add more.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>length demo</title>
  <style>
  body {
    cursor: pointer;
  }
  div {
    width: 50px;
    height: 30px;
    margin: 5px;
    float: left;
    background: green;
  }
  span {
    color: red;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​<span></span>
  <div></div>​
<script>
$( document.body )
  .click(function() {
    $( document.body ).append( $( "<div>" ) );
    var n = $( "div" ).length;
    $( "span" ).text( "There are " + n + " divs." +
      "Click to add more.");
  })
  // Trigger the click to start
  .trigger( "click" );
</script>
​
</body>
</html>
```
     */
    length: number;
    /**
     * Create a new jQuery object with elements added to the set of matched elements.
     * @param selector A string representing a selector expression to find additional elements to add to the set of matched elements.
     * @param context The point in the document at which the selector should begin matching; similar to the context
     *                argument of the $(selector, context) method.
     * @see \`{@link https://api.jquery.com/add/ }\`
     * @since 1.4
     */
    add(selector: JQuery.Selector, context: Element): this;
    // TODO: The return type should reflect newly selected types.
    /**
     * Create a new jQuery object with elements added to the set of matched elements.
     * @param selector_elements_html_selection _&#x40;param_ `selector_elements_html_selection`
     * <br>
     * * `selector` — A string representing a selector expression to find additional elements to add to the set of matched elements. <br>
     * * `elements` — One or more elements to add to the set of matched elements. <br>
     * * `html` — An HTML fragment to add to the set of matched elements. <br>
     * * `selection` — An existing jQuery object to add to the set of matched elements.
     * @see \`{@link https://api.jquery.com/add/ }\`
     * @since 1.0
     * @since 1.3.2
     * @example ​ ````Finds all divs and makes a border.  Then adds all paragraphs to the jQuery object to set their backgrounds yellow.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>add demo</title>
  <style>
  div {
    width: 60px;
    height: 60px;
    margin: 10px;
    float: left;
  }
  p {
    clear: left;
    font-weight: bold;
    font-size: 16px;
    color: blue;
    margin: 0 10px;
    padding: 2px;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<div></div>
<div></div>
<div></div>
<div></div>
<div></div>
<div></div>
​
<p>Added this... (notice no border)</p>
​
<script>
$( "div" ).css( "border", "2px solid red" )
  .add( "p" )
  .css( "background", "yellow" );
</script>
​
</body>
</html>
```
     * @example ​ ````Adds more elements, matched by the given expression, to the set of matched elements.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>add demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p>Hello</p>
<span>Hello Again</span>
​
<script>
$( "p" ).add( "span" ).css( "background", "yellow" );
</script>
​
</body>
</html>
```
     * @example ​ ````Adds more elements, created on the fly, to the set of matched elements.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>add demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p>Hello</p>
​
<script>
$( "p" ).clone().add( "<span>Again</span>" ).appendTo( document.body );
</script>
​
</body>
</html>
```
     * @example ​ ````Adds one or more Elements to the set of matched elements.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>add demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p>Hello</p>
<span id="a">Hello Again</span>
​
<script>
$( "p" ).add( document.getElementById( "a" ) ).css( "background", "yellow" );
</script>
​
</body>
</html>
```
     * @example ​ ````Demonstrates how to add (or push) elements to an existing collection
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>add demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p>Hello</p>
<span id="a">Hello Again</span>
​
<script>
var collection = $( "p" );
// Capture the new collection
collection = collection.add( document.getElementById( "a" ) );
collection.css( "background", "yellow" );
</script>
​
</body>
</html>
```
     */
    add(selector_elements_html_selection: JQuery.Selector | JQuery.TypeOrArray<Element> | JQuery.htmlString | JQuery | JQuery.Node): this;
    /**
     * Add the previous set of elements on the stack to the current set, optionally filtered by a selector.
     * @param selector A string containing a selector expression to match the current set of elements against.
     * @see \`{@link https://api.jquery.com/addBack/ }\`
     * @since 1.8
     * @example ​ ````The .addBack() method causes the previous set of DOM elements in the traversal stack to be added to the current set. In the first example, the top stack contains the set resulting from .find(&quot;p&quot;). In the second example, .addBack() adds the previous set of elements on the stack — in this case $(&quot;div.after-addback&quot;) — to the current set, selecting both the div and its enclosed paragraphs.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>addBack demo</title>
  <style>
  p, div {
    margin: 5px;
    padding: 5px;
  }
  .border {
    border: 2px solid red;
  }
  .background {
    background: yellow;
  }
  .left, .right {
    width: 45%;
    float: left;
  }
  .right {
    margin-left: 3%;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<div class="left">
  <p><strong>Before <code>addBack()</code></strong></p>
  <div class="before-addback">
    <p>First Paragraph</p>
    <p>Second Paragraph</p>
  </div>
</div>
<div class="right">
  <p><strong>After <code>addBack()</code></strong></p>
  <div class="after-addback">
    <p>First Paragraph</p>
    <p>Second Paragraph</p>
  </div>
</div>
​
<script>
$( "div.left, div.right" ).find( "div, div > p" ).addClass( "border" );
​
// First Example
$( "div.before-addback" ).find( "p" ).addClass( "background" );
​
// Second Example
$( "div.after-addback" ).find( "p" ).addBack().addClass( "background" );
</script>
​
</body>
</html>
```
     */
    addBack(selector?: JQuery.Selector): this;
    /**
     * Adds the specified class(es) to each element in the set of matched elements.
     * @param className_function _&#x40;param_ `className_function`
     * <br>
     * * `className` — One or more space-separated classes to be added to the class attribute of each matched element. <br>
     * * `function` — A function returning one or more space-separated class names to be added to the existing class
     *                name(s). Receives the index position of the element in the set and the existing class name(s) as
     *                arguments. Within the function, `this` refers to the current element in the set.
     * @see \`{@link https://api.jquery.com/addClass/ }\`
     * @since 1.0
     * @since 1.4
     * @since 3.3
     * @example ​ ````Add the class &quot;selected&quot; to the matched elements.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>addClass demo</title>
  <style>
  p {
    margin: 8px;
    font-size: 16px;
  }
  .selected {
    color: blue;
  }
  .highlight {
    background: yellow;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p>Hello</p>
<p>and</p>
<p>Goodbye</p>
​
<script>
$( "p" ).last().addClass( "selected" );
</script>
​
</body>
</html>
```
     * @example ​ ````Add the classes &quot;selected&quot; and &quot;highlight&quot; to the matched elements.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>addClass demo</title>
  <style>
  p {
    margin: 8px;
    font-size: 16px;
  }
  .selected {
    color: red;
  }
  .highlight {
    background: yellow;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p>Hello</p>
<p>and</p>
<p>Goodbye</p>
​
<script>
$( "p:last" ).addClass( "selected highlight" );
</script>
​
</body>
</html>
```
     * @example ​ ````Pass in a function to .addClass() to add the &quot;green&quot; class to a div that already has a &quot;red&quot; class.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>addClass demo</title>
  <style>
  div {
    background: white;
  }
  .red {
    background: red;
  }
  .red.green {
    background: green;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
 <div>This div should be white</div>
 <div class="red">This div will be green because it now has the "green" and "red" classes.
   It would be red if the addClass function failed.</div>
 <div>This div should be white</div>
 <p>There are zero green divs</p>
​
<script>
$( "div" ).addClass(function( index, currentClass ) {
  var addedClass;
​
  if ( currentClass === "red" ) {
    addedClass = "green";
    $( "p" ).text( "There is one green div" );
  }
​
  return addedClass;
});
</script>
​
</body>
</html>
```
     */
    addClass(className_function: JQuery.TypeOrArray<string> | ((this: TElement, index: number, currentClassName: string) => string)): this;
    /**
     * Insert content, specified by the parameter, after each element in the set of matched elements.
     * @param contents One or more additional DOM elements, text nodes, arrays of elements and text nodes, HTML strings, or
     *                 jQuery objects to insert after each element in the set of matched elements.
     * @see \`{@link https://api.jquery.com/after/ }\`
     * @since 1.0
     * @example ​ ````Inserts some HTML after all paragraphs.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>after demo</title>
  <style>
  p {
    background: yellow;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p>I would like to say: </p>
​
<script>
$( "p" ).after( "<b>Hello</b>" );
</script>
​
</body>
</html>
```
     * @example ​ ````Inserts a DOM element after all paragraphs.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>after demo</title>
  <style>
  p {
    background: yellow;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p>I would like to say: </p>
​
<script>
$( "p" ).after( document.createTextNode( "Hello" ) );
</script>
​
</body>
</html>
```
     * @example ​ ````Inserts a jQuery object (similar to an Array of DOM Elements) after all paragraphs.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>after demo</title>
  <style>
  p {
    background: yellow;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<b>Hello</b>
<p>I would like to say: </p>
​
<script>
$( "p" ).after( $( "b" ) );
</script>
​
</body>
</html>
```
     */
    after(...contents: Array<JQuery.htmlString | JQuery.TypeOrArray<JQuery.Node | JQuery<JQuery.Node>>>): this;
    /**
     * Insert content, specified by the parameter, after each element in the set of matched elements.
     * @param function_functionｰhtml _&#x40;param_ `function_functionｰhtml`
     * <br>
     * * `function` — A function that returns an HTML string, DOM element(s), text node(s), or jQuery object to insert
     *                after each element in the set of matched elements. Receives the index position of the element in the
     *                set as an argument. Within the function, `this` refers to the current element in the set. <br>
     * * `functionｰhtml` — A function that returns an HTML string, DOM element(s), text node(s), or jQuery object to insert
     *                     after each element in the set of matched elements. Receives the index position of the element in the
     *                     set and the old HTML value of the element as arguments. Within the function, `this` refers to the
     *                     current element in the set.
     * @see \`{@link https://api.jquery.com/after/ }\`
     * @since 1.4
     * @since 1.10
     */
    after(function_functionｰhtml: (this: TElement, index: number, html: string) => JQuery.htmlString | JQuery.TypeOrArray<JQuery.Node | JQuery<JQuery.Node>>): this;
    /**
     * Register a handler to be called when Ajax requests complete. This is an AjaxEvent.
     * @param handler The function to be invoked.
     * @see \`{@link https://api.jquery.com/ajaxComplete/ }\`
     * @since 1.0
     * @example ​ ````Show a message when an Ajax request completes.
```javascript
$( document ).ajaxComplete(function( event, request, settings ) {
  $( "#msg" ).append( "<li>Request Complete.</li>" );
});
```
     */
    ajaxComplete(handler: (this: Document,
                           event: JQuery.TriggeredEvent<Document, undefined, Document, Document>,
                           jqXHR: JQuery.jqXHR,
                           ajaxOptions: JQuery.AjaxSettings) => void | false): this;
    /**
     * Register a handler to be called when Ajax requests complete with an error. This is an Ajax Event.
     * @param handler The function to be invoked.
     * @see \`{@link https://api.jquery.com/ajaxError/ }\`
     * @since 1.0
     * @example ​ ````Show a message when an Ajax request fails.
```javascript
$( document ).ajaxError(function( event, request, settings ) {
  $( "#msg" ).append( "<li>Error requesting page " + settings.url + "</li>" );
});
```
     */
    ajaxError(handler: (this: Document,
                        event: JQuery.TriggeredEvent<Document, undefined, Document, Document>,
                        jqXHR: JQuery.jqXHR,
                        ajaxSettings: JQuery.AjaxSettings,
                        thrownError: string) => void | false): this;
    /**
     * Attach a function to be executed before an Ajax request is sent. This is an Ajax Event.
     * @param handler The function to be invoked.
     * @see \`{@link https://api.jquery.com/ajaxSend/ }\`
     * @since 1.0
     * @example ​ ````Show a message before an Ajax request is sent.
```javascript
$( document ).ajaxSend(function( event, request, settings ) {
  $( "#msg" ).append( "<li>Starting request at " + settings.url + "</li>" );
});
```
     */
    ajaxSend(handler: (this: Document,
                       event: JQuery.TriggeredEvent<Document, undefined, Document, Document>,
                       jqXHR: JQuery.jqXHR,
                       ajaxOptions: JQuery.AjaxSettings) => void | false): this;
    /**
     * Register a handler to be called when the first Ajax request begins. This is an Ajax Event.
     * @param handler The function to be invoked.
     * @see \`{@link https://api.jquery.com/ajaxStart/ }\`
     * @since 1.0
     * @example ​ ````Show a loading message whenever an Ajax request starts (and none is already active).
```javascript
$( document ).ajaxStart(function() {
  $( "#loading" ).show();
});
```
     */
    ajaxStart(handler: (this: Document) => void | false): this;
    /**
     * Register a handler to be called when all Ajax requests have completed. This is an Ajax Event.
     * @param handler The function to be invoked.
     * @see \`{@link https://api.jquery.com/ajaxStop/ }\`
     * @since 1.0
     * @example ​ ````Hide a loading message after all the Ajax requests have stopped.
```javascript
$( document ).ajaxStop(function() {
  $( "#loading" ).hide();
});
```
     */
    ajaxStop(handler: (this: Document) => void | false): this;
    /**
     * Attach a function to be executed whenever an Ajax request completes successfully. This is an Ajax Event.
     * @param handler The function to be invoked.
     * @see \`{@link https://api.jquery.com/ajaxSuccess/ }\`
     * @since 1.0
     * @example ​ ````Show a message when an Ajax request completes successfully.
```javascript
$( document ).ajaxSuccess(function( event, request, settings ) {
  $( "#msg" ).append( "<li>Successful Request!</li>" );
});
```
     */
    ajaxSuccess(handler: (this: Document,
                          event: JQuery.TriggeredEvent<Document, undefined, Document, Document>,
                          jqXHR: JQuery.jqXHR,
                          ajaxOptions: JQuery.AjaxSettings,
                          data: JQuery.PlainObject) => void | false): this;
    /**
     * Perform a custom animation of a set of CSS properties.
     * @param properties An object of CSS properties and values that the animation will move toward.
     * @param duration A string or number determining how long the animation will run.
     * @param easing A string indicating which easing function to use for the transition.
     * @param complete A function to call once the animation is complete, called once per matched element.
     * @see \`{@link https://api.jquery.com/animate/ }\`
     * @since 1.0
     * @example ​ ````An example of using an &#39;easing&#39; function to provide a different style of animation. This will only work if you have a plugin that provides this easing function.  Note, this code will do nothing unless the paragraph element is hidden.
```javascript
$( "p" ).animate({
  opacity: "show"
}, "slow", "easein" );
```
     * @example ​ ````Animate all paragraphs and execute a callback function when the animation is complete.  The first argument is an object of CSS properties, the second specifies that the animation should take 1000 milliseconds to complete, the third states the easing type, and the fourth argument is an anonymous callback function.
```javascript
$( "p" ).animate({
  height: 200,
  width: 400,
  opacity: 0.5
}, 1000, "linear", function() {
  alert( "all done" );
});
```
     */
    animate(properties: JQuery.PlainObject,
            duration: JQuery.Duration,
            easing: string,
            complete?: (this: TElement) => void): this;
    /**
     * Perform a custom animation of a set of CSS properties.
     * @param properties An object of CSS properties and values that the animation will move toward.
     * @param duration_easing _&#x40;param_ `duration_easing`
     * <br>
     * * `duration` — A string or number determining how long the animation will run. <br>
     * * `easing` — A string indicating which easing function to use for the transition.
     * @param complete A function to call once the animation is complete, called once per matched element.
     * @see \`{@link https://api.jquery.com/animate/ }\`
     * @since 1.0
     * @example ​ ````Click the button to animate the div with a number of different properties.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>animate demo</title>
  <style>
  div {
    background-color: #bca;
    width: 100px;
    border: 1px solid green;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<button id="go">&raquo; Run</button>
<div id="block">Hello!</div>
​
<script>
// Using multiple unit types within one animation.
​
$( "#go" ).click(function() {
  $( "#block" ).animate({
    width: "70%",
    opacity: 0.4,
    marginLeft: "0.6in",
    fontSize: "3em",
    borderWidth: "10px"
  }, 1500 );
});
</script>
​
</body>
</html>
```
     * @example ​ ````Animates a div&#39;s left property with a relative value. Click several times on the buttons to see the relative animations queued up.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>animate demo</title>
  <style>
  div {
    position: absolute;
    background-color: #abc;
    left: 50px;
    width: 90px;
    height: 90px;
    margin: 5px;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<button id="left">&laquo;</button>
<button id="right">&raquo;</button>
<div class="block"></div>
​
<script>
$( "#right" ).click(function() {
  $( ".block" ).animate({ "left": "+=50px" }, "slow" );
});
​
$( "#left" ).click(function(){
  $( ".block" ).animate({ "left": "-=50px" }, "slow" );
});
</script>
​
</body>
</html>
```
     * @example ​ ````Animate all paragraphs to toggle both height and opacity, completing the animation within 600 milliseconds.
```javascript
$( "p" ).animate({
  height: "toggle",
  opacity: "toggle"
}, "slow" );
```
     * @example ​ ````Animate all paragraphs to a left style of 50 and opacity of 1 (opaque, visible), completing the animation within 500 milliseconds.
```javascript
$( "p" ).animate({
  left: 50,
  opacity: 1
}, 500 );
```
     */
    animate(properties: JQuery.PlainObject,
            duration_easing: JQuery.Duration | string,
            complete?: (this: TElement) => void): this;
    /**
     * Perform a custom animation of a set of CSS properties.
     * @param properties An object of CSS properties and values that the animation will move toward.
     * @param options A map of additional options to pass to the method.
     * @see \`{@link https://api.jquery.com/animate/ }\`
     * @since 1.0
     * @example ​ ````The first button shows how an unqueued animation works.  It expands the div out to 90% width while the font-size is increasing. Once the font-size change is complete, the border animation will begin.

The second button starts a traditional chained animation, where each animation will start once the previous animation on the element has completed.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>animate demo</title>
  <style>
  div {
    background-color: #bca;
    width: 200px;
    height: 1.1em;
    text-align: center;
    border: 2px solid green;
    margin: 3px;
    font-size: 14px;
  }
  button {
    font-size: 14px;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<button id="go1">&raquo; Animate Block1</button>
<button id="go2">&raquo; Animate Block2</button>
<button id="go3">&raquo; Animate Both</button>
<button id="go4">&raquo; Reset</button>
<div id="block1">Block1</div>
<div id="block2">Block2</div>
​
<script>
$( "#go1" ).click(function() {
  $( "#block1" )
    .animate({
      width: "90%"
    }, {
      queue: false,
      duration: 3000
    })
    .animate({ fontSize: "24px" }, 1500 )
    .animate({ borderRightWidth: "15px" }, 1500 );
});
​
$( "#go2" ).click(function() {
  $( "#block2" )
    .animate({ width: "90%" }, 1000 )
    .animate({ fontSize: "24px" }, 1000 )
    .animate({ borderLeftWidth: "15px" }, 1000 );
});
​
$( "#go3" ).click(function() {
  $( "#go1" ).add( "#go2" ).click();
});
​
$( "#go4" ).click(function() {
  $( "div" ).css({
    width: "",
    fontSize: "",
    borderWidth: ""
  });
});
</script>
​
</body>
</html>
```
     * @example ​ ````Animates the first div&#39;s left property and synchronizes the remaining divs, using the step function to set their left properties at each stage of the animation.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>animate demo</title>
  <style>
  div {
    position: relative;
    background-color: #abc;
    width: 40px;
    height: 40px;
    float: left;
    margin: 5px;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button id="go">Run »</button></p>
<div class="block"></div>
<div class="block"></div>
<div class="block"></div>
<div class="block"></div>
<div class="block"></div>
<div class="block"></div>
​
<script>
$( "#go" ).click(function() {
  $( ".block:first" ).animate({
    left: 100
  }, {
    duration: 1000,
    step: function( now, fx ){
      $( ".block:gt(0)" ).css( "left", now );
    }
  });
});
</script>
​
</body>
</html>
```
     * @example ​ ````Animate the left and opacity style properties of all paragraphs; run the animation outside the queue, so that it will automatically start without waiting for its turn.
```javascript
$( "p" ).animate({
  left: "50px",
  opacity: 1
}, {
  duration: 500,
  queue: false
});
```
     * @example ​ ````Animates all paragraphs to toggle both height and opacity, completing the animation within 600 milliseconds.
```javascript
$( "p" ).animate({
  height: "toggle",
  opacity: "toggle"
}, {
  duration: "slow"
});
```
     * @example ​ ````Use an easing function to provide a different style of animation. This will only work if you have a plugin that provides this easing function.
```javascript
$( "p" ).animate({
  opacity: "show"
}, {
  duration: "slow",
  easing: "easein"
});
```
     */
    animate(properties: JQuery.PlainObject,
            options: JQuery.EffectsOptions<TElement>): this;
    /**
     * Perform a custom animation of a set of CSS properties.
     * @param properties An object of CSS properties and values that the animation will move toward.
     * @param complete A function to call once the animation is complete, called once per matched element.
     * @see \`{@link https://api.jquery.com/animate/ }\`
     * @since 1.0
     */
    animate(properties: JQuery.PlainObject,
            complete?: (this: TElement) => void): this;
    /**
     * Insert content, specified by the parameter, to the end of each element in the set of matched elements.
     * @param contents One or more additional DOM elements, text nodes, arrays of elements and text nodes, HTML strings, or
     *                 jQuery objects to insert at the end of each element in the set of matched elements.
     * @see \`{@link https://api.jquery.com/append/ }\`
     * @since 1.0
     * @example ​ ````Appends some HTML to all paragraphs.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>append demo</title>
  <style>
  p {
    background: yellow;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p>I would like to say: </p>
​
<script>
$( "p" ).append( "<strong>Hello</strong>" );
</script>
​
</body>
</html>
```
     * @example ​ ````Appends an Element to all paragraphs.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>append demo</title>
  <style>
  p {
    background: yellow;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p>I would like to say: </p>
​
<script>
$( "p" ).append( document.createTextNode( "Hello" ) );
</script>
​
</body>
</html>
```
     * @example ​ ````Appends a jQuery object (similar to an Array of DOM Elements) to all paragraphs.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>append demo</title>
  <style>
  p {
    background: yellow;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<strong>Hello world!!!</strong>
<p>I would like to say: </p>
​
<script>
$( "p" ).append( $( "strong" ) );
</script>
​
</body>
</html>
```
     */
    append(...contents: Array<JQuery.htmlString | JQuery.TypeOrArray<JQuery.Node | JQuery<JQuery.Node>>>): this;
    /**
     * Insert content, specified by the parameter, to the end of each element in the set of matched elements.
     * @param funсtion A function that returns an HTML string, DOM element(s), text node(s), or jQuery object to insert at
     *                 the end of each element in the set of matched elements. Receives the index position of the element
     *                 in the set and the old HTML value of the element as arguments. Within the function, `this` refers to
     *                 the current element in the set.
     * @see \`{@link https://api.jquery.com/append/ }\`
     * @since 1.4
     */
    append(funсtion: (this: TElement, index: number, html: string) => JQuery.htmlString | JQuery.TypeOrArray<JQuery.Node | JQuery<JQuery.Node>>): this;
    /**
     * Insert every element in the set of matched elements to the end of the target.
     * @param target A selector, element, HTML string, array of elements, or jQuery object; the matched set of elements
     *               will be inserted at the end of the element(s) specified by this parameter.
     * @see \`{@link https://api.jquery.com/appendTo/ }\`
     * @since 1.0
     * @example ​ ````Append all spans to the element with the ID &quot;foo&quot; (Check append() documentation for more examples)
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>appendTo demo</title>
  <style>
  #foo {
    background: yellow;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<span>I have nothing more to say... </span>
​
<div id="foo">FOO! </div>
​
<script>
$( "span" ).appendTo( "#foo" );
</script>
​
</body>
</html>
```
     */
    appendTo(target: JQuery.Selector | JQuery.htmlString | JQuery.TypeOrArray<Element | DocumentFragment> | JQuery): this;
    /**
     * Set one or more attributes for the set of matched elements.
     * @param attributeName The name of the attribute to set.
     * @param value_function _&#x40;param_ `value_function`
     * <br>
     * * `value` — A value to set for the attribute. If `null`, the specified attribute will be removed (as in \`{@link removeAttr .removeAttr()}`). <br>
     * * `function` — A function returning the value to set. `this` is the current element. Receives the index position of
     *                the element in the set and the old attribute value as arguments.
     * @see \`{@link https://api.jquery.com/attr/ }\`
     * @since 1.0
     * @since 1.1
     * @example ​ ````Set the id for divs based on the position in the page.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>attr demo</title>
  <style>
  div {
    color: blue;
  }
  span {
    color: red;
  }
  b {
    font-weight: bolder;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<div>Zero-th <span></span></div>
<div>First <span></span></div>
<div>Second <span></span></div>
​
<script>
$( "div" )
  .attr( "id", function( arr ) {
    return "div-id" + arr;
  })
  .each(function() {
    $( "span", this ).html( "(id = '<b>" + this.id + "</b>')" );
});
</script>
​
</body>
</html>
```
     * @example ​ ````Set the src attribute from title attribute on the image.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>attr demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<img title="hat.gif">
​
<script>
$( "img" ).attr( "src", function() {
  return "/resources/" + this.title;
});
</script>
​
</body>
</html>
```
     */
    attr(attributeName: string,
         value_function: string | number | null | ((this: TElement, index: number, attr: string) => string | number | void | undefined)): this;
    /**
     * Set one or more attributes for the set of matched elements.
     * @param attributes An object of attribute-value pairs to set.
     * @see \`{@link https://api.jquery.com/attr/ }\`
     * @since 1.0
     * @example ​ ````Set some attributes for all &lt;img&gt;s in the page.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>attr demo</title>
  <style>
  img {
    padding: 10px;
  }
  div {
    color: red;
    font-size: 24px;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<img>
<img>
<img>
​
<div><b>Attribute of Ajax</b></div>
​
<script>
$( "img" ).attr({
  src: "/resources/hat.gif",
  title: "jQuery",
  alt: "jQuery Logo"
});
$( "div" ).text( $( "img" ).attr( "alt" ) );
</script>
​
</body>
</html>
```
     */
    attr(attributes: JQuery.PlainObject): this;
    /**
     * Get the value of an attribute for the first element in the set of matched elements.
     * @param attributeName The name of the attribute to get.
     * @see \`{@link https://api.jquery.com/attr/ }\`
     * @since 1.0
     * @example ​ ````Display the checked attribute and property of a checkbox as it changes.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>attr demo</title>
  <style>
  p {
    margin: 20px 0 0;
  }
  b {
    color: blue;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<input id="check1" type="checkbox" checked="checked">
<label for="check1">Check me</label>
<p></p>
​
<script>
$( "input" )
  .change(function() {
    var $input = $( this );
    $( "p" ).html( ".attr( 'checked' ): <b>" + $input.attr( "checked" ) + "</b><br>" +
      ".prop( 'checked' ): <b>" + $input.prop( "checked" ) + "</b><br>" +
      ".is( ':checked' ): <b>" + $input.is( ":checked" ) + "</b>" );
  })
  .change();
</script>
​
</body>
</html>
```
     * @example ​ ````Find the title attribute of the first &lt;em&gt; in the page.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>attr demo</title>
  <style>
  em {
    color: blue;
    font-weight: bold;
  }
  div {
    color: red;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p>Once there was a <em title="huge, gigantic">large</em> dinosaur...</p>
​
The title of the emphasis is:<div></div>
​
<script>
var title = $( "em" ).attr( "title" );
$( "div" ).text( title );
</script>
​
</body>
</html>
```
     */
    attr(attributeName: string): string | undefined;
    /**
     * Insert content, specified by the parameter, before each element in the set of matched elements.
     * @param contents One or more additional DOM elements, text nodes, arrays of elements and text nodes, HTML strings, or
     *                 jQuery objects to insert before each element in the set of matched elements.
     * @see \`{@link https://api.jquery.com/before/ }\`
     * @since 1.0
     * @example ​ ````Inserts some HTML before all paragraphs.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>before demo</title>
  <style>
  p {
    background: yellow;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p> is what I said...</p>
​
<script>
$( "p" ).before( "<b>Hello</b>" );
</script>
​
</body>
</html>
```
     * @example ​ ````Inserts a DOM element before all paragraphs.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>before demo</title>
  <style>
  p {
    background: yellow;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p> is what I said...</p>
​
<script>
$( "p" ).before( document.createTextNode( "Hello" ) );
</script>
​
</body>
</html>
```
     * @example ​ ````Inserts a jQuery object (similar to an Array of DOM Elements) before all paragraphs.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>before demo</title>
  <style>
  p {
    background: yellow;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p> is what I said...</p><b>Hello</b>
​
<script>
$( "p" ).before( $( "b" ) );
</script>
​
</body>
</html>
```
     */
    before(...contents: Array<JQuery.htmlString | JQuery.TypeOrArray<JQuery.Node | JQuery<JQuery.Node>>>): this;
    /**
     * Insert content, specified by the parameter, before each element in the set of matched elements.
     * @param function_functionｰhtml _&#x40;param_ `function_functionｰhtml`
     * <br>
     * * `function` — A function that returns an HTML string, DOM element(s), text node(s), or jQuery object to insert
     *                before each element in the set of matched elements. Receives the index position of the element in
     *                the set as an argument. Within the function, `this` refers to the current element in the set. <br>
     * * `functionｰhtml` — A function that returns an HTML string, DOM element(s), text node(s), or jQuery object to insert
     *                     before each element in the set of matched elements. Receives the index position of the element in
     *                     the set and the old HTML value of the element as arguments. Within the function, `this` refers to the
     *                     current element in the set.
     * @see \`{@link https://api.jquery.com/before/ }\`
     * @since 1.4
     * @since 1.10
     */
    before(function_functionｰhtml: (this: TElement, index: number, html: string) => JQuery.htmlString | JQuery.TypeOrArray<JQuery.Node | JQuery<JQuery.Node>>): this;
    // [bind() overloads] https://github.com/jquery/api.jquery.com/issues/1048
    /**
     * Attach a handler to an event for the elements.
     * @param eventType A string containing one or more DOM event types, such as "click" or "submit," or custom event names.
     * @param eventData An object containing data that will be passed to the event handler.
     * @param handler A function to execute each time the event is triggered.
     * @see \`{@link https://api.jquery.com/bind/ }\`
     * @since 1.0
     * @since 1.4.3
     * @deprecated ​ Deprecated since 3.0. Use \`{@link on }\`.
     *
     * **Cause**: These event binding methods have been deprecated in favor of the `.on()` and `.off()` methods which can handle both delegated and direct event binding. Although the older methods are still present in jQuery 3.0, they may be removed as early as the next major-version update.
     *
     * **Solution**: Change the method call to use `.on()` or `.off()`, the documentation for the old methods include specific instructions. In general, the `.bind()` and `.unbind()` methods can be renamed directly to `.on()` and `.off()` respectively since the argument orders are identical.
     */
    bind<TType extends string,
         TData>(
        eventType: TType,
        eventData: TData,
        handler: JQuery.TypeEventHandler<TElement, TData, TElement, TElement, TType>
    ): this;
    /**
     * Attach a handler to an event for the elements.
     * @param eventType A string containing one or more DOM event types, such as "click" or "submit," or custom event names.
     * @param handler_preventBubble _&#x40;param_ `handler_preventBubble`
     * <br>
     * * `handler` — A function to execute each time the event is triggered. <br>
     * * `preventBubble` — Setting the third argument to false will attach a function that prevents the default action from
     *                     occurring and stops the event from bubbling. The default is `true`.
     * @see \`{@link https://api.jquery.com/bind/ }\`
     * @since 1.0
     * @since 1.4.3
     * @deprecated ​ Deprecated since 3.0. Use \`{@link on }\`.
     *
     * **Cause**: These event binding methods have been deprecated in favor of the `.on()` and `.off()` methods which can handle both delegated and direct event binding. Although the older methods are still present in jQuery 3.0, they may be removed as early as the next major-version update.
     *
     * **Solution**: Change the method call to use `.on()` or `.off()`, the documentation for the old methods include specific instructions. In general, the `.bind()` and `.unbind()` methods can be renamed directly to `.on()` and `.off()` respectively since the argument orders are identical.
     * @example ​ ````Handle click and double-click for the paragraph.  Note: the coordinates are window relative, so in this case relative to the demo iframe.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>bind demo</title>
  <style>
  p {
    background: yellow;
    font-weight: bold;
    cursor: pointer;
    padding: 5px;
  }
  p.over {
     background: #ccc;
  }
  span {
    color: red;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p>Click or double click here.</p>
<span></span>
​
<script>
$( "p" ).bind( "click", function( event ) {
  var str = "( " + event.pageX + ", " + event.pageY + " )";
  $( "span" ).text( "Click happened! " + str );
});
$( "p" ).bind( "dblclick", function() {
  $( "span" ).text( "Double-click happened in " + this.nodeName );
});
$( "p" ).bind( "mouseenter mouseleave", function( event ) {
  $( this ).toggleClass( "over" );
});
</script>
​
</body>
</html>
```
     * @example ​ ````To display each paragraph&#39;s text in an alert box whenever it is clicked:
```javascript
$( "p" ).bind( "click", function() {
  alert( $( this ).text() );
});
```
     * @example ​ ````Cancel a default action and prevent it from bubbling up by returning false:
```javascript
$( "form" ).bind( "submit", function() {
  return false;
})
```
     * @example ​ ````Cancel only the default action by using the .preventDefault() method.
```javascript
$( "form" ).bind( "submit", function( event ) {
  event.preventDefault();
});
```
     * @example ​ ````Stop an event from bubbling without preventing the default action by using the .stopPropagation() method.
```javascript
$( "form" ).bind( "submit", function( event ) {
  event.stopPropagation();
});
```
     * @example ​ ````Bind custom events.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>bind demo</title>
  <style>
  p {
    color: red;
  }
  span {
    color: blue;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p>Has an attached custom event.</p>
<button>Trigger custom event</button>
<span style="display: none;"></span>
​
<script>
$( "p" ).bind( "myCustomEvent", function( e, myName, myValue ) {
  $( this ).text( myName + ", hi there!" );
  $( "span" )
    .stop()
    .css( "opacity", 1 )
    .text( "myName = " + myName )
    .fadeIn( 30 )
    .fadeOut( 1000 );
  });
$( "button" ).click(function() {
  $( "p" ).trigger( "myCustomEvent", [ "John" ] );
});
</script>
​
</body>
</html>
```
     */
    bind<TType extends string>(
        eventType: TType,
        handler_preventBubble: JQuery.TypeEventHandler<TElement, undefined, TElement, TElement, TType> |
                               false |
                               null |
                               undefined
    ): this;
    /**
     * Attach a handler to an event for the elements.
     * @param events An object containing one or more DOM event types and functions to execute for them.
     * @see \`{@link https://api.jquery.com/bind/ }\`
     * @since 1.4
     * @deprecated ​ Deprecated since 3.0. Use \`{@link on }\`.
     *
     * **Cause**: These event binding methods have been deprecated in favor of the `.on()` and `.off()` methods which can handle both delegated and direct event binding. Although the older methods are still present in jQuery 3.0, they may be removed as early as the next major-version update.
     *
     * **Solution**: Change the method call to use `.on()` or `.off()`, the documentation for the old methods include specific instructions. In general, the `.bind()` and `.unbind()` methods can be renamed directly to `.on()` and `.off()` respectively since the argument orders are identical.
     * @example ​ ````Bind multiple events simultaneously.
```javascript
$( "div.test" ).bind({
  click: function() {
    $( this ).addClass( "active" );
  },
  mouseenter: function() {
    $( this ).addClass( "inside" );
  },
  mouseleave: function() {
    $( this ).removeClass( "inside" );
  }
});
```
     */
    bind(events: JQuery.TypeEventHandlers<TElement, undefined, TElement, TElement>): this;
    /**
     * Bind an event handler to the "blur" JavaScript event, or trigger that event on an element.
     * @param eventData An object containing data that will be passed to the event handler.
     * @param handler A function to execute each time the event is triggered.
     * @see \`{@link https://api.jquery.com/blur/ }\`
     * @since 1.4.3
     * @deprecated ​ Deprecated since 3.3. Use \`{@link on }\` or \`{@link trigger }\`.
     *
     * **Cause**: The `.on()` and `.trigger()` methods can set an event handler or generate an event for any event type, and should be used instead of the shortcut methods. This message also applies to the other event shorthands, including: blur, focus, focusin, focusout, resize, scroll, dblclick, mousedown, mouseup, mousemove, mouseover, mouseout, mouseenter, mouseleave, change, select, submit, keydown, keypress, keyup, and contextmenu.
     *
     * **Solution**: Instead of `.click(fn)` use `.on("click", fn)`. Instead of `.click()` use `.trigger("click")`.
     */
    blur<TData>(eventData: TData,
                handler: JQuery.TypeEventHandler<TElement, TData, TElement, TElement, 'blur'>): this;
    /**
     * Bind an event handler to the "blur" JavaScript event, or trigger that event on an element.
     * @param handler A function to execute each time the event is triggered.
     * @see \`{@link https://api.jquery.com/blur/ }\`
     * @since 1.0
     * @deprecated ​ Deprecated since 3.3. Use \`{@link on }\` or \`{@link trigger }\`.
     *
     * **Cause**: The `.on()` and `.trigger()` methods can set an event handler or generate an event for any event type, and should be used instead of the shortcut methods. This message also applies to the other event shorthands, including: blur, focus, focusin, focusout, resize, scroll, dblclick, mousedown, mouseup, mousemove, mouseover, mouseout, mouseenter, mouseleave, change, select, submit, keydown, keypress, keyup, and contextmenu.
     *
     * **Solution**: Instead of `.click(fn)` use `.on("click", fn)`. Instead of `.click()` use `.trigger("click")`.
     * @example ​ ````To trigger the blur event on all paragraphs:
```javascript
$( "p" ).blur();
```
     */
    blur(handler?: JQuery.TypeEventHandler<TElement, null, TElement, TElement, 'blur'> |
                   false): this;
    /**
     * Bind an event handler to the "change" JavaScript event, or trigger that event on an element.
     * @param eventData An object containing data that will be passed to the event handler.
     * @param handler A function to execute each time the event is triggered.
     * @see \`{@link https://api.jquery.com/change/ }\`
     * @since 1.4.3
     * @deprecated ​ Deprecated since 3.3. Use \`{@link on }\` or \`{@link trigger }\`.
     *
     * **Cause**: The `.on()` and `.trigger()` methods can set an event handler or generate an event for any event type, and should be used instead of the shortcut methods. This message also applies to the other event shorthands, including: blur, focus, focusin, focusout, resize, scroll, dblclick, mousedown, mouseup, mousemove, mouseover, mouseout, mouseenter, mouseleave, change, select, submit, keydown, keypress, keyup, and contextmenu.
     *
     * **Solution**: Instead of `.click(fn)` use `.on("click", fn)`. Instead of `.click()` use `.trigger("click")`.
     */
    change<TData>(eventData: TData,
                  handler: JQuery.TypeEventHandler<TElement, TData, TElement, TElement, 'change'>): this;
    /**
     * Bind an event handler to the "change" JavaScript event, or trigger that event on an element.
     * @param handler A function to execute each time the event is triggered.
     * @see \`{@link https://api.jquery.com/change/ }\`
     * @since 1.0
     * @deprecated ​ Deprecated since 3.3. Use \`{@link on }\` or \`{@link trigger }\`.
     *
     * **Cause**: The `.on()` and `.trigger()` methods can set an event handler or generate an event for any event type, and should be used instead of the shortcut methods. This message also applies to the other event shorthands, including: blur, focus, focusin, focusout, resize, scroll, dblclick, mousedown, mouseup, mousemove, mouseover, mouseout, mouseenter, mouseleave, change, select, submit, keydown, keypress, keyup, and contextmenu.
     *
     * **Solution**: Instead of `.click(fn)` use `.on("click", fn)`. Instead of `.click()` use `.trigger("click")`.
     * @example ​ ````Attaches a change event to the select that gets the text for each selected option and writes them in the div.  It then triggers the event for the initial text draw.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>change demo</title>
  <style>
  div {
    color: red;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<select name="sweets" multiple="multiple">
  <option>Chocolate</option>
  <option selected="selected">Candy</option>
  <option>Taffy</option>
  <option selected="selected">Caramel</option>
  <option>Fudge</option>
  <option>Cookie</option>
</select>
<div></div>
​
<script>
$( "select" )
  .change(function () {
    var str = "";
    $( "select option:selected" ).each(function() {
      str += $( this ).text() + " ";
    });
    $( "div" ).text( str );
  })
  .change();
</script>
​
</body>
</html>
```
     * @example ​ ````To add a validity test to all text input elements:
```javascript
$( "input[type='text']" ).change(function() {
  // Check input( $( this ).val() ) for validity here
});
```
     */
    change(handler?: JQuery.TypeEventHandler<TElement, null, TElement, TElement, 'change'> |
                     false): this;
    /**
     * Get the children of each element in the set of matched elements, optionally filtered by a selector.
     * @param selector A string containing a selector expression to match elements against.
     * @see \`{@link https://api.jquery.com/children/ }\`
     * @since 1.0
     * @example ​ ````Find all children of the clicked element.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>children demo</title>
  <style>
  body {
    font-size: 16px;
    font-weight: bolder;
  }
  div {
    width: 130px;
    height: 82px;
    margin: 10px;
    float: left;
    border: 1px solid blue;
    padding: 4px;
  }
  #container {
    width: auto;
    height: 105px;
    margin: 0;
    float: none;
    border: none;
  }
  .hilite {
    border-color: red;
  }
  #results {
    display: block;
    color: red;
  }
  p, span, em, a, b, button {
    border: 1px solid transparent;
  }
  p {
    margin: 10px;
  }
  span {
    color: blue;
  }
  input {
    width: 100px;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<div id="container">
  <div>
    <p>This <span>is the <em>way</em> we</span>
      write <em>the</em> demo,</p>
  </div>
​
  <div>
    <a href="#"><b>w</b>rit<b>e</b></a> the <span>demo,</span> <button>write
    the</button> demo,
  </div>
​
  <div>
    This <span>the way we <em>write</em> the <em>demo</em> so</span>
    <input type="text" value="early"> in
  </div>
​
  <p>
    <span>t</span>he <span>m</span>orning.
    <span id="results">Found <span>0</span> children in <span>TAG</span>.</span>
  </p>
</div>
​
<script>
$( "#container" ).click(function ( event ) {
  $( "*" ).removeClass( "hilite" );
  var kids = $( event.target ).children();
  var len = kids.addClass( "hilite" ).length;
​
  $( "#results span:first" ).text( len );
  $( "#results span:last" ).text( event.target.tagName );
​
  event.preventDefault();
});
</script>
​
</body>
</html>
```
     * @example ​ ````Find all children of each div.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>children demo</title>
  <style>
  body {
    font-size: 16px;
    font-weight: bolder;
  }
  span {
    color: blue;
  }
  p {
    margin: 5px 0;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p>Hello (this is a paragraph)</p>
​
<div><span>Hello Again (this span is a child of the a div)</span></div>
<p>And <span>Again</span> (in another paragraph)</p>
​
<div>And One Last <span>Time</span> (most text directly in a div)</div>
​
<script>
$( "div" ).children().css( "border-bottom", "3px double red" );
</script>
​
</body>
</html>
```
     * @example ​ ````Find all children with a class &quot;selected&quot; of each div.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>children demo</title>
  <style>
  body {
    font-size: 16px;
    font-weight: bolder;
  }
  p {
    margin: 5px 0;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<div>
  <span>Hello</span>
  <p class="selected">Hello Again</p>
  <div class="selected">And Again</div>
  <p>And One Last Time</p>
</div>
​
<script>
$( "div" ).children( ".selected" ).css( "color", "blue" );
</script>
​
</body>
</html>
```
     */
    children(selector?: JQuery.Selector): this;
    /**
     * Remove from the queue all items that have not yet been run.
     * @param queueName A string containing the name of the queue. Defaults to fx, the standard effects queue.
     * @see \`{@link https://api.jquery.com/clearQueue/ }\`
     * @since 1.4
     * @example ​ ````Empty the queue.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>clearQueue demo</title>
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
  var myDiv = $( "div" );
  myDiv.show( "slow" );
  myDiv.animate({
    left:"+=200"
  }, 5000 );
​
  myDiv.queue(function() {
    var that = $( this );
    that.addClass( "newcolor" );
    that.dequeue();
  });
​
  myDiv.animate({
    left:"-=200"
  }, 1500 );
  myDiv.queue(function() {
    var that = $( this );
    that.removeClass( "newcolor" );
    that.dequeue();
  });
  myDiv.slideUp();
});
​
$( "#stop" ).click(function() {
  var myDiv = $( "div" );
  myDiv.clearQueue();
  myDiv.stop();
});
</script>
​
</body>
</html>
```
     */
    clearQueue(queueName?: string): this;
    /**
     * Bind an event handler to the "click" JavaScript event, or trigger that event on an element.
     * @param eventData An object containing data that will be passed to the event handler.
     * @param handler A function to execute each time the event is triggered.
     * @see \`{@link https://api.jquery.com/click/ }\`
     * @since 1.4.3
     * @deprecated ​ Deprecated since 3.3. Use \`{@link on }\` or \`{@link trigger }\`.
     *
     * **Cause**: The `.on()` and `.trigger()` methods can set an event handler or generate an event for any event type, and should be used instead of the shortcut methods. This message also applies to the other event shorthands, including: blur, focus, focusin, focusout, resize, scroll, dblclick, mousedown, mouseup, mousemove, mouseover, mouseout, mouseenter, mouseleave, change, select, submit, keydown, keypress, keyup, and contextmenu.
     *
     * **Solution**: Instead of `.click(fn)` use `.on("click", fn)`. Instead of `.click()` use `.trigger("click")`.
     */
    click<TData>(eventData: TData,
                 handler: JQuery.TypeEventHandler<TElement, TData, TElement, TElement, 'click'>): this;
    /**
     * Bind an event handler to the "click" JavaScript event, or trigger that event on an element.
     * @param handler A function to execute each time the event is triggered.
     * @see \`{@link https://api.jquery.com/click/ }\`
     * @since 1.0
     * @deprecated ​ Deprecated since 3.3. Use \`{@link on }\` or \`{@link trigger }\`.
     *
     * **Cause**: The `.on()` and `.trigger()` methods can set an event handler or generate an event for any event type, and should be used instead of the shortcut methods. This message also applies to the other event shorthands, including: blur, focus, focusin, focusout, resize, scroll, dblclick, mousedown, mouseup, mousemove, mouseover, mouseout, mouseenter, mouseleave, change, select, submit, keydown, keypress, keyup, and contextmenu.
     *
     * **Solution**: Instead of `.click(fn)` use `.on("click", fn)`. Instead of `.click()` use `.trigger("click")`.
     * @example ​ ````Hide paragraphs on a page when they are clicked:
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>click demo</title>
  <style>
  p {
    color: red;
    margin: 5px;
    cursor: pointer;
  }
  p:hover {
    background: yellow;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p>First Paragraph</p>
<p>Second Paragraph</p>
<p>Yet one more Paragraph</p>
​
<script>
$( "p" ).click(function() {
  $( this ).slideUp();
});
</script>
​
</body>
</html>
```
     * @example ​ ````Trigger the click event on all of the paragraphs on the page:
```javascript
$( "p" ).click();
```
     */
    click(handler?: JQuery.TypeEventHandler<TElement, null, TElement, TElement, 'click'> |
                    false): this;
    /**
     * Create a deep copy of the set of matched elements.
     * @param withDataAndEvents A Boolean indicating whether event handlers and data should be copied along with the elements. The
     *                          default value is false. *In jQuery 1.5.0 the default value was incorrectly true; it was changed back
     *                          to false in 1.5.1 and up.
     * @param deepWithDataAndEvents A Boolean indicating whether event handlers and data for all children of the cloned element should
     *                              be copied. By default its value matches the first argument's value (which defaults to false).
     * @see \`{@link https://api.jquery.com/clone/ }\`
     * @since 1.0
     * @since 1.5
     * @example ​ ````Clones all b elements (and selects the clones) and prepends them to all paragraphs.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>clone demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<b>Hello</b><p>, how are you?</p>
​
<script>
$( "b" ).clone().prependTo( "p" );
</script>
​
</body>
</html>
```
     */
    clone(withDataAndEvents?: boolean, deepWithDataAndEvents?: boolean): this;
    /**
     * For each element in the set, get the first element that matches the selector by testing the element itself and traversing up through its ancestors in the DOM tree.
     * @param selector A string containing a selector expression to match elements against.
     * @param context A DOM element within which a matching element may be found.
     * @see \`{@link https://api.jquery.com/closest/ }\`
     * @since 1.4
     */
    closest(selector: JQuery.Selector, context: Element): this;
    /**
     * For each element in the set, get the first element that matches the selector by testing the element itself and traversing up through its ancestors in the DOM tree.
     * @param selector_selection_element _&#x40;param_ `selector_selection_element`
     * <br>
     * * `selector` — A string containing a selector expression to match elements against. <br>
     * * `selection` — A jQuery object to match elements against. <br>
     * * `element` — An element to match elements against.
     * @see \`{@link https://api.jquery.com/closest/ }\`
     * @since 1.3
     * @since 1.6
     * @example ​ ````Show how event delegation can be done with closest. The closest list element toggles a yellow background when it or its descendent is clicked.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>closest demo</title>
  <style>
  li {
    margin: 3px;
    padding: 3px;
    background: #EEEEEE;
  }
  li.highlight {
    background: yellow;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<ul>
  <li><b>Click me!</b></li>
  <li>You can also <b>Click me!</b></li>
</ul>
​
<script>
$( document ).on( "click", function( event ) {
  $( event.target ).closest( "li" ).toggleClass( "highlight" );
});
</script>
​
</body>
</html>
```
     * @example ​ ````Pass a jQuery object to closest. The closest list element toggles a yellow background when it or its descendent is clicked.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>closest demo</title>
  <style>
  li {
    margin: 3px;
    padding: 3px;
    background: #EEEEEE;
  }
  li.highlight {
    background: yellow;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<ul>
  <li><b>Click me!</b></li>
  <li>You can also <b>Click me!</b></li>
</ul>
​
<script>
var listElements = $( "li" ).css( "color", "blue" );
$( document ).on( "click", function( event ) {
  $( event.target ).closest( listElements ).toggleClass( "highlight" );
});
</script>
​
</body>
</html>
```
     */
    closest(selector_selection_element: JQuery.Selector | Element | JQuery): this;
    /**
     * Get the children of each element in the set of matched elements, including text and comment nodes.
     * @see \`{@link https://api.jquery.com/contents/ }\`
     * @since 1.2
     * @example ​ ````Find all the text nodes inside a paragraph and wrap them with a bold tag.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>contents demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p>Hello <a href="https://johnresig.com/">John</a>, how are you doing?</p>
​
<script>
$( "p" )
  .contents()
  .filter(function(){
    return this.nodeType !== 1;
  })
  .wrap( "<b></b>" );
</script>
​
</body>
</html>
```
     * @example ​ ````Change the background color of links inside of an iframe.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>contents demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<iframe src="https://api.jquery.com/" width="80%" height="600" id="frameDemo"></iframe>
​
<script>
$( "#frameDemo" ).contents().find( "a" ).css( "background-color", "#BADA55" );
</script>
​
</body>
</html>
```
     */
    contents(): JQuery<TElement | Text | Comment | Document>;
    /**
     * Bind an event handler to the "contextmenu" JavaScript event, or trigger that event on an element.
     * @param eventData An object containing data that will be passed to the event handler.
     * @param handler A function to execute each time the event is triggered.
     * @see \`{@link https://api.jquery.com/contextmenu/ }\`
     * @since 1.4.3
     * @deprecated ​ Deprecated since 3.3. Use \`{@link on }\` or \`{@link trigger }\`.
     *
     * **Cause**: The `.on()` and `.trigger()` methods can set an event handler or generate an event for any event type, and should be used instead of the shortcut methods. This message also applies to the other event shorthands, including: blur, focus, focusin, focusout, resize, scroll, dblclick, mousedown, mouseup, mousemove, mouseover, mouseout, mouseenter, mouseleave, change, select, submit, keydown, keypress, keyup, and contextmenu.
     *
     * **Solution**: Instead of `.click(fn)` use `.on("click", fn)`. Instead of `.click()` use `.trigger("click")`.
     */
    contextmenu<TData>(eventData: TData,
                       handler: JQuery.TypeEventHandler<TElement, TData, TElement, TElement, 'contextmenu'>): this;
    /**
     * Bind an event handler to the "contextmenu" JavaScript event, or trigger that event on an element.
     * @param handler A function to execute each time the event is triggered.
     * @see \`{@link https://api.jquery.com/contextmenu/ }\`
     * @since 1.0
     * @deprecated ​ Deprecated since 3.3. Use \`{@link on }\` or \`{@link trigger }\`.
     *
     * **Cause**: The `.on()` and `.trigger()` methods can set an event handler or generate an event for any event type, and should be used instead of the shortcut methods. This message also applies to the other event shorthands, including: blur, focus, focusin, focusout, resize, scroll, dblclick, mousedown, mouseup, mousemove, mouseover, mouseout, mouseenter, mouseleave, change, select, submit, keydown, keypress, keyup, and contextmenu.
     *
     * **Solution**: Instead of `.click(fn)` use `.on("click", fn)`. Instead of `.click()` use `.trigger("click")`.
     * @example ​ ````To show a &quot;Hello World!&quot; alert box when the contextmenu event is triggered on a paragraph on the page:
```javascript
$( "p" ).contextmenu(function() {
  alert( "Hello World!" );
});
```
     * @example ​ ````Right click to toggle background color.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>contextmenu demo</title>
  <style>
  div {
    background: blue;
    color: white;
    height: 100px;
    width: 150px;
 }
  div.contextmenu {
    background: yellow;
    color: black;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<div></div>
<span>Right click the block</span>
​
<script>
var div = $( "div:first" );
div.contextmenu(function() {
  div.toggleClass( "contextmenu" );
});
</script>
​
</body>
</html>
```
     */
    contextmenu(handler?: JQuery.TypeEventHandler<TElement, null, TElement, TElement, 'contextmenu'> |
                          false): this;
    /**
     * Set one or more CSS properties for the set of matched elements.
     * @param propertyName A CSS property name.
     * @param value_function _&#x40;param_ `value_function`
     * <br>
     * * `value` — A value to set for the property. <br>
     * * `function` — A function returning the value to set. `this` is the current element. Receives the index position of
     *                the element in the set and the old value as arguments.
     * @see \`{@link https://api.jquery.com/css/ }\`
     * @since 1.0
     * @since 1.4
     * @example ​ ````Change the color of any paragraph to red on mouseover event.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>css demo</title>
  <style>
  p {
    color: blue;
    width: 200px;
    font-size: 14px;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
  <p>Just roll the mouse over me.</p>
​
  <p>Or me to see a color change.</p>
​
<script>
$( "p" ).on( "mouseover", function() {
  $( this ).css( "color", "red" );
});
</script>
​
</body>
</html>
```
     * @example ​ ````Increase the width of #box by 200 pixels the first time it is clicked.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>css demo</title>
  <style>
  #box {
    background: black;
    color: snow;
    width: 100px;
    padding: 10px;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<div id="box">Click me to grow</div>
​
<script>
$( "#box" ).one( "click", function() {
  $( this ).css( "width", "+=200" );
});
</script>
​
</body>
</html>
```
     * @example ​ ````Highlight a clicked word in the paragraph.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>css demo</title>
  <style>
  p {
    color: blue;
    font-weight: bold;
    cursor: pointer;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p>
  Once upon a time there was a man
  who lived in a pizza parlor. This
  man just loved pizza and ate it all
  the time.  He went on to be the
  happiest man in the world.  The end.
</p>
​
<script>
var words = $( "p" ).first().text().split( /\s+/ );
var text = words.join( "</span> <span>" );
$( "p" ).first().html( "<span>" + text + "</span>" );
$( "span" ).on( "click", function() {
  $( this ).css( "background-color", "yellow" );
});
</script>
​
</body>
</html>
```
     */
    css(propertyName: string,
        value_function: string | number | ((this: TElement, index: number, value: string) => string | number | void | undefined)): this;
    /**
     * Set one or more CSS properties for the set of matched elements.
     * @param properties An object of property-value pairs to set.
     * @see \`{@link https://api.jquery.com/css/ }\`
     * @since 1.0
     * @example ​ ````Change the font weight and background color on mouseenter and mouseleave.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>css demo</title>
  <style>
  p {
    color: green;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p>Move the mouse over a paragraph.</p>
<p>Like this one or the one above.</p>
​
<script>
$( "p" )
  .on( "mouseenter", function() {
    $( this ).css({
      "background-color": "yellow",
      "font-weight": "bolder"
    });
  })
  .on( "mouseleave", function() {
    var styles = {
      backgroundColor : "#ddd",
      fontWeight: ""
    };
    $( this ).css( styles );
  });
</script>
​
</body>
</html>
```
     * @example ​ ````Increase the size of a div when you click it.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>css demo</title>
  <style>
  div {
    width: 20px;
    height: 15px;
    background-color: #f33;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<div>click</div>
<div>click</div>
​
<script>
$( "div" ).on( "click", function() {
  $( this ).css({
    width: function( index, value ) {
      return parseFloat( value ) * 1.2;
    },
    height: function( index, value ) {
      return parseFloat( value ) * 1.2;
    }
  });
});
</script>
​
</body>
</html>
```
     */
    css(properties: JQuery.PlainObject<string | number | ((this: TElement, index: number, value: string) => string | number | void | undefined)>): this;
    /**
     * Get the computed style properties for the first element in the set of matched elements.
     * @param propertyName A CSS property.
     * @see \`{@link https://api.jquery.com/css/ }\`
     * @since 1.0
     * @example ​ ````Get the background color of a clicked div.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>css demo</title>
  <style>
  div {
    width: 60px;
    height: 60px;
    margin: 5px;
    float: left;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<span id="result">&nbsp;</span>
<div style="background-color:blue;"></div>
<div style="background-color:rgb(15,99,30);"></div>
<div style="background-color:#123456;"></div>
<div style="background-color:#f11;"></div>
​
<script>
$( "div" ).click(function() {
  var color = $( this ).css( "background-color" );
  $( "#result" ).html( "That div is <span style='color:" +
    color + ";'>" + color + "</span>." );
});
</script>
​
</body>
</html>
```
     */
    css(propertyName: string): string;
    /**
     * Get the computed style properties for the first element in the set of matched elements.
     * @param propertyNames An array of one or more CSS properties.
     * @see \`{@link https://api.jquery.com/css/ }\`
     * @since 1.9
     * @example ​ ````Get the width, height, text color, and background color of a clicked div.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>css demo</title>
  <style>
  div {
    height: 50px;
    margin: 5px;
    padding: 5px;
    float: left;
  }
  #box1 {
    width: 50px;
    color: yellow;
    background-color: blue;
  }
  #box2 {
    width: 80px;
    color: rgb(255, 255, 255);
    background-color: rgb(15, 99, 30);
  }
  #box3 {
    width: 40px;
    color: #fcc;
    background-color: #123456;
  }
  #box4 {
    width: 70px;
    background-color: #f11;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p id="result">&nbsp;</p>
<div id="box1">1</div>
<div id="box2">2</div>
<div id="box3">3</div>
<div id="box4">4</div>
​
<script>
$( "div" ).click(function() {
  var html = [ "The clicked div has the following styles:" ];
​
  var styleProps = $( this ).css([
    "width", "height", "color", "background-color"
  ]);
  $.each( styleProps, function( prop, value ) {
    html.push( prop + ": " + value );
  });
​
  $( "#result" ).html( html.join( "<br>" ) );
});
</script>
​
</body>
</html>
```
     */
    css(propertyNames: string[]): JQuery.PlainObject<string>;
    /**
     * Store arbitrary data associated with the matched elements.
     * @param key A string naming the piece of data to set.
     * @param value The new data value; this can be any Javascript type except `undefined`.
     * @see \`{@link https://api.jquery.com/data/ }\`
     * @since 1.2.3
     * @example ​ ````Store then retrieve a value from the div element.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>data demo</title>
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
$( "div" ).data( "test", { first: 16, last: "pizza!" } );
$( "span:first" ).text( $( "div" ).data( "test" ).first );
$( "span:last" ).text( $( "div" ).data( "test" ).last );
</script>
​
</body>
</html>
```
     */
    data(key: string, value: string | number | boolean | symbol | object | null): this;
    /**
     * Store arbitrary data associated with the matched elements.
     * @param obj An object of key-value pairs of data to update.
     * @see \`{@link https://api.jquery.com/data/ }\`
     * @since 1.4.3
     */
    data(obj: JQuery.PlainObject): this;
    /**
     * Return the value at the named data store for the first element in the jQuery collection, as set by data(name, value) or by an HTML5 data-* attribute.
     * @param key Name of the data stored.
     * @param value `undefined` is not recognized as a data value. Calls such as `.data( "name", undefined )`
     *              will return the jQuery object that it was called on, allowing for chaining.
     * @see \`{@link https://api.jquery.com/data/ }\`
     * @since 1.2.3
     */
    // `unified-signatures` is disabled so that behavior when passing `undefined` to `value` can be documented. Unifying the signatures
    // results in potential confusion for users from an unexpected parameter.
    // tslint:disable-next-line:unified-signatures
    data(key: string, value: undefined): any;
    /**
     * Return the value at the named data store for the first element in the jQuery collection, as set by data(name, value) or by an HTML5 data-* attribute.
     * @param key Name of the data stored.
     * @see \`{@link https://api.jquery.com/data/ }\`
     * @since 1.2.3
     * @example ​ ````Get the data named &quot;blah&quot; stored at for an element.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>data demo</title>
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
$( "button" ).click(function() {
  var value;
​
  switch ( $( "button" ).index( this ) ) {
    case 0 :
      value = $( "div" ).data( "blah" );
      break;
    case 1 :
      $( "div" ).data( "blah", "hello" );
      value = "Stored!";
      break;
    case 2 :
      $( "div" ).data( "blah", 86 );
      value = "Stored!";
      break;
    case 3 :
      $( "div" ).removeData( "blah" );
      value = "Removed!";
      break;
  }
​
  $( "span" ).text( "" + value );
});
</script>
​
</body>
</html>
```
     */
    data(key: string): any;
    /**
     * Return the value at the named data store for the first element in the jQuery collection, as set by data(name, value) or by an HTML5 data-* attribute.
     * @see \`{@link https://api.jquery.com/data/ }\`
     * @since 1.4
     */
    data(): JQuery.PlainObject;
    /**
     * Bind an event handler to the "dblclick" JavaScript event, or trigger that event on an element.
     * @param eventData An object containing data that will be passed to the event handler.
     * @param handler A function to execute each time the event is triggered.
     * @see \`{@link https://api.jquery.com/dblclick/ }\`
     * @since 1.4.3
     * @deprecated ​ Deprecated since 3.3. Use \`{@link on }\` or \`{@link trigger }\`.
     *
     * **Cause**: The `.on()` and `.trigger()` methods can set an event handler or generate an event for any event type, and should be used instead of the shortcut methods. This message also applies to the other event shorthands, including: blur, focus, focusin, focusout, resize, scroll, dblclick, mousedown, mouseup, mousemove, mouseover, mouseout, mouseenter, mouseleave, change, select, submit, keydown, keypress, keyup, and contextmenu.
     *
     * **Solution**: Instead of `.click(fn)` use `.on("click", fn)`. Instead of `.click()` use `.trigger("click")`.
     */
    dblclick<TData>(eventData: TData,
                    handler: JQuery.TypeEventHandler<TElement, TData, TElement, TElement, 'dblclick'>): this;
    /**
     * Bind an event handler to the "dblclick" JavaScript event, or trigger that event on an element.
     * @param handler A function to execute each time the event is triggered.
     * @see \`{@link https://api.jquery.com/dblclick/ }\`
     * @since 1.0
     * @deprecated ​ Deprecated since 3.3. Use \`{@link on }\` or \`{@link trigger }\`.
     *
     * **Cause**: The `.on()` and `.trigger()` methods can set an event handler or generate an event for any event type, and should be used instead of the shortcut methods. This message also applies to the other event shorthands, including: blur, focus, focusin, focusout, resize, scroll, dblclick, mousedown, mouseup, mousemove, mouseover, mouseout, mouseenter, mouseleave, change, select, submit, keydown, keypress, keyup, and contextmenu.
     *
     * **Solution**: Instead of `.click(fn)` use `.on("click", fn)`. Instead of `.click()` use `.trigger("click")`.
     * @example ​ ````To bind a &quot;Hello World!&quot; alert box to the dblclick event on every paragraph on the page:
```javascript
$( "p" ).dblclick(function() {
  alert( "Hello World!" );
});
```
     * @example ​ ````Double click to toggle background color.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>dblclick demo</title>
  <style>
  div {
    background: blue;
    color: white;
    height: 100px;
    width: 150px;
 }
  div.dbl {
    background: yellow;
    color: black;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<div></div>
<span>Double click the block</span>
​
<script>
var divdbl = $( "div:first" );
divdbl.dblclick(function() {
  divdbl.toggleClass( "dbl" );
});
</script>
​
</body>
</html>
```
     */
    dblclick(handler?: JQuery.TypeEventHandler<TElement, null, TElement, TElement, 'dblclick'> |
                       false): this;
    /**
     * Set a timer to delay execution of subsequent items in the queue.
     * @param duration An integer indicating the number of milliseconds to delay execution of the next item in the queue.
     * @param queueName A string containing the name of the queue. Defaults to fx, the standard effects queue.
     * @see \`{@link https://api.jquery.com/delay/ }\`
     * @since 1.4
     * @example ​ ````Animate the hiding and showing of two divs, delaying the first before showing it.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>delay demo</title>
  <style>
  div {
    position: absolute;
    width: 60px;
    height: 60px;
    float: left;
  }
  .first {
    background-color: #3f3;
    left: 0;
  }
  .second {
    background-color: #33f;
    left: 80px;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button>Run</button></p>
<div class="first"></div>
<div class="second"></div>
​
<script>
$( "button" ).click(function() {
  $( "div.first" ).slideUp( 300 ).delay( 800 ).fadeIn( 400 );
  $( "div.second" ).slideUp( 300 ).fadeIn( 400 );
});
</script>
​
</body>
</html>
```
     */
    delay(duration: JQuery.Duration, queueName?: string): this;
    /**
     * Attach a handler to one or more events for all elements that match the selector, now or in the future, based on a specific set of root elements.
     * @param selector A selector to filter the elements that trigger the event.
     * @param eventType A string containing one or more space-separated JavaScript event types, such as "click" or
     *                  "keydown," or custom event names.
     * @param eventData An object containing data that will be passed to the event handler.
     * @param handler A function to execute each time the event is triggered.
     * @see \`{@link https://api.jquery.com/delegate/ }\`
     * @since 1.4.2
     * @deprecated ​ Deprecated since 3.0. Use \`{@link on }\`.
     *
     * **Cause**: These event binding methods have been deprecated in favor of the `.on()` and `.off()` methods which can handle both delegated and direct event binding. Although the older methods are still present in jQuery 3.0, they may be removed as early as the next major-version update.
     *
     * **Solution**: Change the method call to use `.on()` or `.off()`, the documentation for the old methods include specific instructions. In general, the `.bind()` and `.unbind()` methods can be renamed directly to `.on()` and `.off()` respectively since the argument orders are identical.
     */
    delegate<TType extends string,
             TData>(
        selector: JQuery.Selector,
        eventType: TType,
        eventData: TData,
        handler: JQuery.TypeEventHandler<TElement, TData, any, any, TType>
    ): this;
    /**
     * Attach a handler to one or more events for all elements that match the selector, now or in the future, based on a specific set of root elements.
     * @param selector A selector to filter the elements that trigger the event.
     * @param eventType A string containing one or more space-separated JavaScript event types, such as "click" or
     *                  "keydown," or custom event names.
     * @param handler A function to execute each time the event is triggered.
     * @see \`{@link https://api.jquery.com/delegate/ }\`
     * @since 1.4.2
     * @deprecated ​ Deprecated since 3.0. Use \`{@link on }\`.
     *
     * **Cause**: These event binding methods have been deprecated in favor of the `.on()` and `.off()` methods which can handle both delegated and direct event binding. Although the older methods are still present in jQuery 3.0, they may be removed as early as the next major-version update.
     *
     * **Solution**: Change the method call to use `.on()` or `.off()`, the documentation for the old methods include specific instructions. In general, the `.bind()` and `.unbind()` methods can be renamed directly to `.on()` and `.off()` respectively since the argument orders are identical.
     * @example ​ ````Click a paragraph to add another. Note that .delegate() attaches a click event handler to all paragraphs - even new ones.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>delegate demo</title>
  <style>
  p {
    background: yellow;
    font-weight: bold;
    cursor: pointer;
    padding: 5px;
  }
  p.over {
    background: #ccc;
  }
  span {
    color: red;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p>Click me!</p>
​
<span></span>
​
<script>
$( "body" ).delegate( "p", "click", function() {
  $( this ).after( "<p>Another paragraph!</p>" );
});
</script>
​
</body>
</html>
```
     * @example ​ ````To display each paragraph&#39;s text in an alert box whenever it is clicked:
```javascript
$( "body" ).delegate( "p", "click", function() {
  alert( $( this ).text() );
});
```
     * @example ​ ````To cancel a default action and prevent it from bubbling up, return false:
```javascript
$( "body" ).delegate( "a", "click", function() {
  return false;
});
```
     * @example ​ ````To cancel only the default action by using the preventDefault method.
```javascript
$( "body" ).delegate( "a", "click", function( event ) {
  event.preventDefault();
});
```
     * @example ​ ````Can bind custom events too.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>delegate demo</title>
  <style>
  p {
    color: red;
  }
  span {
    color: blue;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p>Has an attached custom event.</p>
<button>Trigger custom event</button>
<span style="display:none;"></span>
​
<script>
$( "body" ).delegate( "p", "myCustomEvent", function( e, myName, myValue ) {
  $( this ).text( "Hi there!" );
  $( "span" )
    .stop()
    .css( "opacity", 1 )
    .text( "myName = " + myName )
    .fadeIn( 30 )
    .fadeOut( 1000 );
});
$( "button" ).click(function() {
  $( "p" ).trigger( "myCustomEvent" );
});
</script>
​
</body>
</html>
```
     */
    delegate<TType extends string>(
        selector: JQuery.Selector,
        eventType: TType,
        handler: JQuery.TypeEventHandler<TElement, undefined, any, any, TType> |
                 false
    ): this;
    /**
     * Attach a handler to one or more events for all elements that match the selector, now or in the future, based on a specific set of root elements.
     * @param selector A selector to filter the elements that trigger the event.
     * @param events A plain object of one or more event types and functions to execute for them.
     * @see \`{@link https://api.jquery.com/delegate/ }\`
     * @since 1.4.3
     * @deprecated ​ Deprecated since 3.0. Use \`{@link on }\`.
     *
     * **Cause**: These event binding methods have been deprecated in favor of the `.on()` and `.off()` methods which can handle both delegated and direct event binding. Although the older methods are still present in jQuery 3.0, they may be removed as early as the next major-version update.
     *
     * **Solution**: Change the method call to use `.on()` or `.off()`, the documentation for the old methods include specific instructions. In general, the `.bind()` and `.unbind()` methods can be renamed directly to `.on()` and `.off()` respectively since the argument orders are identical.
     */
    delegate(selector: JQuery.Selector,
             events: JQuery.TypeEventHandlers<TElement, undefined, any, any>
    ): this;
    /**
     * Execute the next function on the queue for the matched elements.
     * @param queueName A string containing the name of the queue. Defaults to fx, the standard effects queue.
     * @see \`{@link https://api.jquery.com/dequeue/ }\`
     * @since 1.2
     * @example ​ ````Use dequeue to end a custom queue function which allows the queue to keep going.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>dequeue demo</title>
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
    .animate({ left:"+=200px" }, 2000 )
    .animate({ top:"0px" }, 600 )
    .queue(function() {
      $( this ).toggleClass( "red" ).dequeue();
    })
    .animate({ left:"10px", top:"30px" }, 700 );
});
</script>
​
</body>
</html>
```
     */
    dequeue(queueName?: string): this;
    /**
     * Remove the set of matched elements from the DOM.
     * @param selector A selector expression that filters the set of matched elements to be removed.
     * @see \`{@link https://api.jquery.com/detach/ }\`
     * @since 1.4
     * @example ​ ````Detach all paragraphs from the DOM
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>detach demo</title>
  <style>
  p {
    background: yellow;
    margin: 6px 0;
  }
  p.off {
    background: black;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p>Hello</p>
how are
<p>you?</p>
<button>Attach/detach paragraphs</button>
​
<script>
$( "p" ).click(function() {
  $( this ).toggleClass( "off" );
});
var p;
$( "button" ).click(function() {
  if ( p ) {
    p.appendTo( "body" );
    p = null;
  } else {
    p = $( "p" ).detach();
  }
});
</script>
​
</body>
</html>
```
     */
    detach(selector?: JQuery.Selector): this;
    /**
     * Iterate over a jQuery object, executing a function for each matched element.
     * @param funсtion A function to execute for each matched element.
     * @see \`{@link https://api.jquery.com/each/ }\`
     * @since 1.0
     * @example ​ ````Iterate over three divs and sets their color property.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>each demo</title>
  <style>
  div {
    color: red;
    text-align: center;
    cursor: pointer;
    font-weight: bolder;
    width: 300px;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<div>Click here</div>
<div>to iterate through</div>
<div>these divs.</div>
​
<script>
$( document.body ).click(function() {
  $( "div" ).each(function( i ) {
    if ( this.style.color !== "blue" ) {
      this.style.color = "blue";
    } else {
      this.style.color = "";
    }
  });
});
</script>
​
</body>
</html>
```
     * @example ​ ````To access a jQuery object instead of the regular DOM element, use $( this ). For example:
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>each demo</title>
  <style>
  ul {
    font-size: 18px;
    margin: 0;
  }
  span {
    color: blue;
    text-decoration: underline;
    cursor: pointer;
  }
  .example {
    font-style: italic;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
To do list: <span>(click here to change)</span>
<ul>
  <li>Eat</li>
  <li>Sleep</li>
  <li>Be merry</li>
</ul>
​
<script>
$( "span" ).click(function() {
  $( "li" ).each(function() {
    $( this ).toggleClass( "example" );
  });
});
</script>
​
</body>
</html>
```
     * @example ​ ````Use return false to break out of each() loops early.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>each demo</title>
  <style>
  div {
    width: 40px;
    height: 40px;
    margin: 5px;
    float: left;
    border: 2px blue solid;
    text-align: center;
  }
  span {
    color: red;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<button>Change colors</button>
<span></span>
<div></div>
<div></div>
<div></div>
<div></div>
<div id="stop">Stop here</div>
<div></div>
<div></div>
<div></div>
​
<script>
$( "button" ).click(function() {
  $( "div" ).each(function( index, element ) {
    // element == this
    $( element ).css( "backgroundColor", "yellow" );
    if ( $( this ).is( "#stop" ) ) {
      $( "span" ).text( "Stopped at div index #" + index );
      return false;
    }
  });
});
</script>
​
</body>
</html>
```
     */
    each(funсtion: (this: TElement, index: number, element: TElement) => void | false): this;
    /**
     * Remove all child nodes of the set of matched elements from the DOM.
     * @see \`{@link https://api.jquery.com/empty/ }\`
     * @since 1.0
     * @example ​ ````Removes all child nodes (including text nodes) from all paragraphs
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>empty demo</title>
  <style>
  p {
    background: yellow;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p>
  Hello, <span>Person</span> <em>and person</em>.
</p>
​
<button>Call empty() on above paragraph</button>
​
<script>
$( "button" ).click(function() {
  $( "p" ).empty();
});
</script>
​
</body>
</html>
```
     */
    empty(): this;
    /**
     * End the most recent filtering operation in the current chain and return the set of matched elements to its previous state.
     * @see \`{@link https://api.jquery.com/end/ }\`
     * @since 1.0
     * @example ​ ````Selects all paragraphs, finds span elements inside these, and reverts the selection back to the paragraphs.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>end demo</title>
  <style>
  p, div {
    margin: 1px;
    padding: 1px;
    font-weight: bold;
    font-size: 16px;
  }
  div {
    color: blue;
  }
  b {
    color: red;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p>
  Hi there <span>how</span> are you <span>doing</span>?
</p>
​
<p>
  This <span>span</span> is one of
  several <span>spans</span> in this
  <span>sentence</span>.
</p>
​
<div>
  Tags in jQuery object initially: <b></b>
</div>
​
<div>
  Tags in jQuery object after find: <b></b>
</div>
​
<div>
  Tags in jQuery object after end: <b></b>
</div>
​
<script>
jQuery.fn.showTags = function( n ) {
  var tags = this.map(function() {
    return this.tagName;
  })
  .get()
  .join( ", " );
  $( "b:eq( " + n + " )" ).text( tags );
  return this;
};
​
$( "p" )
  .showTags( 0 )
  .find( "span" )
    .showTags( 1 )
    .css( "background", "yellow" )
  .end()
  .showTags( 2 )
  .css( "font-style", "italic" );
</script>
​
</body>
</html>
```
     * @example ​ ````Selects all paragraphs, finds span elements inside these, and reverts the selection back to the paragraphs.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>end demo</title>
  <style>
  p {
    margin: 10px;
    padding: 10px;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><span>Hello</span>, how are you?</p>
​
<script>
$( "p" )
  .find( "span" )
  .end()
  .css( "border", "2px red solid" );
</script>
​
</body>
</html>
```
     */
    end(): this;
    /**
     * Reduce the set of matched elements to the one at the specified index.
     * @param index An integer indicating the 0-based position of the element.
     *              An integer indicating the position of the element, counting backwards from the last element in the set.
     * @see \`{@link https://api.jquery.com/eq/ }\`
     * @since 1.1.2
     * @since 1.4
     * @example ​ ````Turn the div with index 2 blue by adding an appropriate class.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>eq demo</title>
  <style>
  div {
    width: 60px;
    height: 60px;
    margin: 10px;
    float: left;
    border: 2px solid blue;
  }
  .blue {
    background: blue;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<div></div>
<div></div>
<div></div>
<div></div>
<div></div>
<div></div>
​
<script>
$( "body" ).find( "div" ).eq( 2 ).addClass( "blue" );
</script>
​
</body>
</html>
```
     */
    eq(index: number): this;
    /**
     * Merge the contents of an object onto the jQuery prototype to provide new jQuery instance methods.
     * @param obj An object to merge onto the jQuery prototype.
     * @see \`{@link https://api.jquery.com/jQuery.fn.extend/ }\`
     * @since 1.0
     * @example ​ ````Add two methods to the jQuery prototype ($.fn) object and then use one of them.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.fn.extend demo</title>
  <style>
  label {
    display: block;
    margin: .5em;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<label><input type="checkbox" name="foo"> Foo</label>
<label><input type="checkbox" name="bar"> Bar</label>
​
<script>
jQuery.fn.extend({
  check: function() {
    return this.each(function() {
      this.checked = true;
    });
  },
  uncheck: function() {
    return this.each(function() {
      this.checked = false;
    });
  }
});
​
// Use the newly created .check() method
$( "input[type='checkbox']" ).check();
</script>
​
</body>
</html>
```
     */
    extend(obj: object): this;
    /**
     * Display the matched elements by fading them to opaque.
     * @param duration A string or number determining how long the animation will run.
     * @param easing A string indicating which easing function to use for the transition.
     * @param complete A function to call once the animation is complete, called once per matched element.
     * @see \`{@link https://api.jquery.com/fadeIn/ }\`
     * @since 1.4.3
     */
    fadeIn(duration: JQuery.Duration, easing: string, complete?: (this: TElement) => void): this;
    /**
     * Display the matched elements by fading them to opaque.
     * @param duration_easing _&#x40;param_ `duration_easing`
     * <br>
     * * `duration` — A string or number determining how long the animation will run. <br>
     * * `easing` — A string indicating which easing function to use for the transition.
     * @param complete A function to call once the animation is complete, called once per matched element.
     * @see \`{@link https://api.jquery.com/fadeIn/ }\`
     * @since 1.0
     * @since 1.4.3
     * @example ​ ````Fades a red block in over the text. Once the animation is done, it quickly fades in more text on top.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>fadeIn demo</title>
  <style>
  p {
    position: relative;
    width: 400px;
    height: 90px;
  }
  div {
    position: absolute;
    width: 400px;
    height: 65px;
    font-size: 36px;
    text-align: center;
    color: yellow;
    background: red;
    padding-top: 25px;
    top: 0;
    left: 0;
    display: none;
  }
  span {
    display: none;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p>
  Let it be known that the party of the first part
  and the party of the second part are henceforth
  and hereto directed to assess the allegations
  for factual correctness... (<a href="#">click!</a>)
  <div><span>CENSORED!</span></div>
</p>
​
<script>
$( "a" ).click(function() {
  $( "div" ).fadeIn( 3000, function() {
    $( "span" ).fadeIn( 100 );
  });
  return false;
});
</script>
​
</body>
</html>
```
     */
    fadeIn(duration_easing: JQuery.Duration | string, complete: (this: TElement) => void): this;
    /**
     * Display the matched elements by fading them to opaque.
     * @param duration_easing_complete_options _&#x40;param_ `duration_easing_complete_options`
     * <br>
     * * `duration` — A string or number determining how long the animation will run. <br>
     * * `easing` — A string indicating which easing function to use for the transition. <br>
     * * `complete` — A function to call once the animation is complete, called once per matched element. <br>
     * * `options` — A map of additional options to pass to the method.
     * @see \`{@link https://api.jquery.com/fadeIn/ }\`
     * @since 1.0
     * @since 1.4.3
     * @example ​ ````Animates hidden divs to fade in one by one, completing each animation within 600 milliseconds.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>fadeIn demo</title>
  <style>
  span {
    color: red;
    cursor: pointer;
  }
  div {
    margin: 3px;
    width: 80px;
    display: none;
    height: 80px;
    float: left;
  }
  #one {
    background: #f00;
  }
  #two {
    background: #0f0;
  }
  #three {
    background: #00f;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<span>Click here...</span>
<div id="one"></div>
<div id="two"></div>
<div id="three"></div>
​
<script>
$( document.body ).click(function() {
  $( "div:hidden:first" ).fadeIn( "slow" );
});
</script>
​
</body>
</html>
```
     */
    fadeIn(duration_easing_complete_options?: JQuery.Duration | string | ((this: TElement) => void) | JQuery.EffectsOptions<TElement>): this;
    /**
     * Hide the matched elements by fading them to transparent.
     * @param duration A string or number determining how long the animation will run.
     * @param easing A string indicating which easing function to use for the transition.
     * @param complete A function to call once the animation is complete, called once per matched element.
     * @see \`{@link https://api.jquery.com/fadeOut/ }\`
     * @since 1.4.3
     * @example ​ ````Fades out two divs, one with a &quot;linear&quot; easing and one with the default, &quot;swing,&quot; easing.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>fadeOut demo</title>
  <style>
  .box,
  button {
    float: left;
    margin: 5px 10px 5px 0;
  }
  .box {
    height: 80px;
    width: 80px;
    background: #090;
  }
  #log {
    clear: left;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<button id="btn1">fade out</button>
<button id="btn2">show</button>
​
<div id="log"></div>
​
<div id="box1" class="box">linear</div>
<div id="box2" class="box">swing</div>
​
<script>
$( "#btn1" ).click(function() {
  function complete() {
    $( "<div>" ).text( this.id ).appendTo( "#log" );
  }
  $( "#box1" ).fadeOut( 1600, "linear", complete );
  $( "#box2" ).fadeOut( 1600, complete );
});
​
$( "#btn2" ).click(function() {
  $( "div" ).show();
  $( "#log" ).empty();
});
</script>
​
</body>
</html>
```
     */
    fadeOut(duration: JQuery.Duration, easing: string, complete?: (this: TElement) => void): this;
    /**
     * Hide the matched elements by fading them to transparent.
     * @param duration_easing _&#x40;param_ `duration_easing`
     * <br>
     * * `duration` — A string or number determining how long the animation will run. <br>
     * * `easing` — A string indicating which easing function to use for the transition.
     * @param complete A function to call once the animation is complete, called once per matched element.
     * @see \`{@link https://api.jquery.com/fadeOut/ }\`
     * @since 1.0
     * @since 1.4.3
     * @example ​ ````Fades out spans in one section that you click on.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>fadeOut demo</title>
  <style>
  span {
    cursor: pointer;
  }
  span.hilite {
    background: yellow;
  }
  div {
    display: inline;
    color: red;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<h3>Find the modifiers - <div></div></h3>
<p>
  If you <span>really</span> want to go outside
  <span>in the cold</span> then make sure to wear
  your <span>warm</span> jacket given to you by
  your <span>favorite</span> teacher.
</p>
​
<script>
$( "span" ).click(function() {
  $( this ).fadeOut( 1000, function() {
    $( "div" ).text( "'" + $( this ).text() + "' has faded!" );
    $( this ).remove();
  });
});
$( "span" ).hover(function() {
  $( this ).addClass( "hilite" );
}, function() {
  $( this ).removeClass( "hilite" );
});
</script>
​
</body>
</html>
```
     */
    fadeOut(duration_easing: JQuery.Duration | string, complete: (this: TElement) => void): this;
    /**
     * Hide the matched elements by fading them to transparent.
     * @param duration_easing_complete_options _&#x40;param_ `duration_easing_complete_options`
     * <br>
     * * `duration` — A string or number determining how long the animation will run. <br>
     * * `easing` — A string indicating which easing function to use for the transition. <br>
     * * `complete` — A function to call once the animation is complete, called once per matched element. <br>
     * * `options` — A map of additional options to pass to the method.
     * @see \`{@link https://api.jquery.com/fadeOut/ }\`
     * @since 1.0
     * @since 1.4.3
     * @example ​ ````Animates all paragraphs to fade out, completing the animation within 600 milliseconds.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>fadeOut demo</title>
  <style>
  p {
    font-size: 150%;
    cursor: pointer;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p>
  If you click on this paragraph
  you'll see it just fade away.
</p>
​
<script>
$( "p" ).click(function() {
  $( "p" ).fadeOut( "slow" );
});
</script>
​
</body>
</html>
```
     */
    fadeOut(duration_easing_complete_options?: JQuery.Duration | string | ((this: TElement) => void) | JQuery.EffectsOptions<TElement>): this;
    /**
     * Adjust the opacity of the matched elements.
     * @param duration A string or number determining how long the animation will run.
     * @param opacity A number between 0 and 1 denoting the target opacity.
     * @param easing A string indicating which easing function to use for the transition.
     * @param complete A function to call once the animation is complete, called once per matched element.
     * @see \`{@link https://api.jquery.com/fadeTo/ }\`
     * @since 1.4.3
     */
    fadeTo(duration: JQuery.Duration, opacity: number, easing: string, complete?: (this: TElement) => void): this;
    /**
     * Adjust the opacity of the matched elements.
     * @param duration A string or number determining how long the animation will run.
     * @param opacity A number between 0 and 1 denoting the target opacity.
     * @param complete A function to call once the animation is complete, called once per matched element.
     * @see \`{@link https://api.jquery.com/fadeTo/ }\`
     * @since 1.0
     * @example ​ ````Animates first paragraph to fade to an opacity of 0.33 (33%, about one third visible), completing the animation within 600 milliseconds.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>fadeTo demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p>
Click this paragraph to see it fade.
</p>
​
<p>
Compare to this one that won't fade.
</p>
​
<script>
$( "p:first" ).click(function() {
  $( this ).fadeTo( "slow", 0.33 );
});
</script>
​
</body>
</html>
```
     * @example ​ ````Fade div to a random opacity on each click, completing the animation within 200 milliseconds.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>fadeTo demo</title>
  <style>
  p {
    width: 80px;
    margin: 0;
    padding: 5px;
  }
  div {
    width: 40px;
    height: 40px;
    position: absolute;
  }
  #one {
    top: 0;
    left: 0;
    background: #f00;
  }
  #two {
    top: 20px;
    left: 20px;
    background: #0f0;
  }
  #three {
    top: 40px;
    left:40px;
    background:#00f;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p>And this is the library that John built...</p>
​
<div id="one"></div>
<div id="two"></div>
<div id="three"></div>
​
<script>
$( "div" ).click(function() {
  $( this ).fadeTo( "fast", Math.random() );
});
</script>
​
</body>
</html>
```
     * @example ​ ````Find the right answer! The fade will take 250 milliseconds and change various styles when it completes.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>fadeTo demo</title>
  <style>
  div, p {
    width: 80px;
    height: 40px;
    top: 0;
    margin: 0;
    position: absolute;
    padding-top: 8px;
  }
  p {
    background: #fcc;
    text-align: center;
  }
  div {
    background: blue;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p>Wrong</p>
<div></div>
<p>Wrong</p>
<div></div>
<p>Right!</p>
<div></div>
​
<script>
var getPos = function( n ) {
  return (Math.floor( n ) * 90) + "px";
};
$( "p" ).each(function( n ) {
  var r = Math.floor( Math.random() * 3 );
  var tmp = $( this ).text();
  $( this ).text( $( "p:eq(" + r + ")" ).text() );
  $( "p:eq(" + r + ")" ).text( tmp );
  $( this ).css( "left", getPos( n ) );
});
$( "div" )
  .each(function( n ) {
    $( this ).css( "left", getPos( n ) );
  })
  .css( "cursor", "pointer" )
  .click( function() {
    $( this ).fadeTo( 250, 0.25, function() {
      $( this )
        .css( "cursor", "" )
        .prev()
          .css({
            "font-weight": "bolder",
            "font-style": "italic"
          });
    });
  });
</script>
​
</body>
</html>
```
     */
    fadeTo(duration: JQuery.Duration, opacity: number, complete?: (this: TElement) => void): this;
    /**
     * Display or hide the matched elements by animating their opacity.
     * @param duration A string or number determining how long the animation will run.
     * @param easing A string indicating which easing function to use for the transition.
     * @param complete A function to call once the animation is complete, called once per matched element.
     * @see \`{@link https://api.jquery.com/fadeToggle/ }\`
     * @since 1.4.4
     * @example ​ ````Fades first paragraph in or out, completing the animation within 600 milliseconds and using a linear easing. Fades last paragraph in or out for 200 milliseconds, inserting a &quot;finished&quot; message upon completion.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>fadeToggle demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<button>fadeToggle p1</button>
<button>fadeToggle p2</button>
<p>This paragraph has a slow, linear fade.</p>
<p>This paragraph has a fast animation.</p>
<div id="log"></div>
​
<script>
$( "button:first" ).click(function() {
  $( "p:first" ).fadeToggle( "slow", "linear" );
});
$( "button:last" ).click(function() {
  $( "p:last" ).fadeToggle( "fast", function() {
    $( "#log" ).append( "<div>finished</div>" );
  });
});
</script>
​
</body>
</html>
```
     */
    fadeToggle(duration: JQuery.Duration, easing: string, complete?: (this: TElement) => void): this;
    /**
     * Display or hide the matched elements by animating their opacity.
     * @param duration_easing _&#x40;param_ `duration_easing`
     * <br>
     * * `duration` — A string or number determining how long the animation will run. <br>
     * * `easing` — A string indicating which easing function to use for the transition.
     * @param complete A function to call once the animation is complete, called once per matched element.
     * @see \`{@link https://api.jquery.com/fadeToggle/ }\`
     * @since 1.0
     * @since 1.4.3
     * @example ​ ````Fades first paragraph in or out, completing the animation within 600 milliseconds and using a linear easing. Fades last paragraph in or out for 200 milliseconds, inserting a &quot;finished&quot; message upon completion.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>fadeToggle demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<button>fadeToggle p1</button>
<button>fadeToggle p2</button>
<p>This paragraph has a slow, linear fade.</p>
<p>This paragraph has a fast animation.</p>
<div id="log"></div>
​
<script>
$( "button:first" ).click(function() {
  $( "p:first" ).fadeToggle( "slow", "linear" );
});
$( "button:last" ).click(function() {
  $( "p:last" ).fadeToggle( "fast", function() {
    $( "#log" ).append( "<div>finished</div>" );
  });
});
</script>
​
</body>
</html>
```
     */
    fadeToggle(duration_easing: JQuery.Duration | string, complete: (this: TElement) => void): this;
    /**
     * Display or hide the matched elements by animating their opacity.
     * @param duration_easing_complete_options _&#x40;param_ `duration_easing_complete_options`
     * <br>
     * * `duration` — A string or number determining how long the animation will run. <br>
     * * `easing` — A string indicating which easing function to use for the transition. <br>
     * * `complete` — A function to call once the animation is complete, called once per matched element. <br>
     * * `options` — A map of additional options to pass to the method.
     * @see \`{@link https://api.jquery.com/fadeToggle/ }\`
     * @since 1.0
     * @since 1.4.3
     */
    fadeToggle(duration_easing_complete_options?: JQuery.Duration | string | ((this: TElement) => void) | JQuery.EffectsOptions<TElement>): this;
    /**
     * Reduce the set of matched elements to those that match the selector or pass the function's test.
     * @param selector_elements_selection_function _&#x40;param_ `selector_elements_selection_function`
     * <br>
     * * `selector` — A string containing a selector expression to match the current set of elements against. <br>
     * * `elements` — One or more DOM elements to match the current set of elements against. <br>
     * * `selection` — An existing jQuery object to match the current set of elements against. <br>
     * * `function` — A function used as a test for each element in the set. this is the current DOM element.
     * @see \`{@link https://api.jquery.com/filter/ }\`
     * @since 1.0
     * @since 1.4
     * @example ​ ````Change the color of all divs; then add a border to those with a &quot;middle&quot; class.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>filter demo</title>
  <style>
  div {
    width: 60px;
    height: 60px;
    margin: 5px;
    float: left;
    border: 2px white solid;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<div></div>
<div class="middle"></div>
<div class="middle"></div>
<div class="middle"></div>
<div class="middle"></div>
<div></div>
​
<script>
$( "div" )
  .css( "background", "#c8ebcc" )
  .filter( ".middle" )
    .css( "border-color", "red" );
</script>
​
</body>
</html>
```
     * @example ​ ````Change the color of all divs; then add a border to the second one (index == 1) and the div with an id of &quot;fourth.&quot;
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>filter demo</title>
  <style>
  div {
    width: 60px;
    height: 60px;
    margin: 5px;
    float: left;
    border: 3px white solid;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<div id="first"></div>
<div id="second"></div>
<div id="third"></div>
<div id="fourth"></div>
<div id="fifth"></div>
<div id="sixth"></div>
​
<script>
$( "div" )
  .css( "background", "#b4b0da" )
  .filter(function( index ) {
    return index === 1 || $( this ).attr( "id" ) === "fourth";
  })
    .css( "border", "3px double red" );
</script>
​
</body>
</html>
```
     * @example ​ ````Select all divs and filter the selection with a DOM element, keeping only the one with an id of &quot;unique&quot;.
```javascript
$( "div" ).filter( document.getElementById( "unique" ) );
```
     * @example ​ ````Select all divs and filter the selection with a jQuery object, keeping only the one with an id of &quot;unique&quot;.
```javascript
$( "div" ).filter( $( "#unique" ) );
```
     */
    filter(selector_elements_selection_function:
        JQuery.Selector |
        JQuery.TypeOrArray<Element> |
        JQuery |
        ((this: TElement, index: number, element: TElement) => boolean)
    ): this;
    /**
     * Get the descendants of each element in the current set of matched elements, filtered by a selector, jQuery object, or element.
     * @param selector_element _&#x40;param_ `selector_element`
     * <br>
     * * `selector` — A string containing a selector expression to match elements against. <br>
     * * `element` — An element or a jQuery object to match elements against.
     * @see \`{@link https://api.jquery.com/find/ }\`
     * @since 1.0
     * @since 1.6
     * @example ​ ````Starts with all paragraphs and searches for descendant span elements, same as $( &quot;p span&quot; )
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>find demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><span>Hello</span>, how are you?</p>
<p>Me? I'm <span>good</span>.</p>
​
<script>
$( "p" ).find( "span" ).css( "color", "red" );
</script>
​
</body>
</html>
```
     * @example ​ ````A selection using a jQuery collection of all span tags. Only spans within p tags are changed to red while others are left blue.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>find demo</title>
  <style>
  span {
    color: blue;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><span>Hello</span>, how are you?</p>
<p>Me? I'm <span>good</span>.</p>
<div>Did you <span>eat</span> yet?</div>
​
<script>
var spans = $( "span" );
$( "p" ).find( spans ).css( "color", "red" );
</script>
​
</body>
</html>
```
     * @example ​ ````Add spans around each word then add a hover and italicize words with the letter t.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>find demo</title>
  <style>
  p {
    font-size: 20px;
    width: 200px;
    color: blue;
    font-weight: bold;
    margin: 0 10px;
  }
  .hilite {
    background: yellow;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p>
  When the day is short
  find that which matters to you
  or stop believing
</p>
​
<script>
var newText = $( "p" ).text().split( " " ).join( "</span> <span>" );
newText = "<span>" + newText + "</span>";
​
$( "p" )
  .html( newText )
  .find( "span" )
    .hover(function() {
      $( this ).addClass( "hilite" );
    }, function() {
      $( this ).removeClass( "hilite" );
    })
  .end()
  .find( ":contains('t')" )
    .css({
      "font-style": "italic",
      "font-weight": "bolder"
    });
</script>
​
</body>
</html>
```
     */
    find(selector_element: JQuery.Selector | Element | JQuery): this;
    /**
     * Stop the currently-running animation, remove all queued animations, and complete all animations for the matched elements.
     * @param queue The name of the queue in which to stop animations.
     * @see \`{@link https://api.jquery.com/finish/ }\`
     * @since 1.9
     * @example ​ ````Click the Go button once to start the animation, and then click the other buttons to see how they affect the current and queued animations.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>finish demo</title>
  <style>
  .box {
    position: absolute;
    top: 10px;
    left: 10px;
    width: 15px;
    height: 15px;
    background: black;
  }
  #path {
    height: 244px;
    font-size: 70%;
    border-left: 2px dashed red;
    border-bottom: 2px dashed green;
    border-right: 2px dashed blue;
  }
  button {
    width: 12em;
    display: block;
    text-align: left;
    margin: 0 auto;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<div class="box"></div>
<div id="path">
  <button id="go">Go</button>
  <br>
  <button id="bstt" class="b">.stop( true,true )</button>
  <button id="bcf" class="b">.clearQueue().finish()</button>
  <br>
  <button id="bstf" class="b">.stop( true, false )</button>
  <button id="bcs" class="b">.clearQueue().stop()</button>
  <br>
  <button id="bsff" class="b">.stop( false, false )</button>
  <button id="bs" class="b">.stop()</button>
  <br>
  <button id="bsft" class="b">.stop( false, true )</button>
  <br>
  <button id="bf" class="b">.finish()</button>
</div>
​
<script>
var horiz = $( "#path" ).width() - 20,
  vert = $( "#path" ).height() - 20;
​
var btns = {
  bstt: function() {
    $( "div.box" ).stop( true, true );
  },
  bs: function() {
    $( "div.box" ).stop();
  },
  bsft: function() {
    $( "div.box" ).stop( false, true );
  },
  bf: function() {
    $( "div.box" ).finish();
  },
  bcf: function() {
    $( "div.box" ).clearQueue().finish();
  },
  bsff: function() {
    $( "div.box" ).stop( false, false );
  },
  bstf: function() {
    $( "div.box" ).stop( true, false );
  },
  bcs: function() {
    $( "div.box" ).clearQueue().stop();
  }
};
​
$( "button.b" ).on( "click", function() {
  btns[ this.id ]();
});
​
$( "#go" ).on( "click", function() {
  $( ".box" )
    .clearQueue()
    .stop()
    .css({
      left: 10,
      top: 10
    })
    .animate({
      top: vert
    }, 3000 )
    .animate({
      left: horiz
    }, 3000 )
    .animate({
      top: 10
    }, 3000 );
});
</script>
​
</body>
</html>
```
     */
    finish(queue?: string): this;
    /**
     * Reduce the set of matched elements to the first in the set.
     * @see \`{@link https://api.jquery.com/first/ }\`
     * @since 1.4
     * @example ​ ````Highlight the first span in a paragraph.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>first demo</title>
  <style>
  .highlight{
    background-color: yellow
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p>
  <span>Look:</span>
  <span>This is some text in a paragraph.</span>
  <span>This is a note about it.</span>
</p>
​
<script>
$( "p span" ).first().addClass( "highlight" );
</script>
​
</body>
</html>
```
     */
    first(): this;
    /**
     * Bind an event handler to the "focus" JavaScript event, or trigger that event on an element.
     * @param eventData An object containing data that will be passed to the event handler.
     * @param handler A function to execute each time the event is triggered.
     * @see \`{@link https://api.jquery.com/focus/ }\`
     * @since 1.4.3
     * @deprecated ​ Deprecated since 3.3. Use \`{@link on }\` or \`{@link trigger }\`.
     *
     * **Cause**: The `.on()` and `.trigger()` methods can set an event handler or generate an event for any event type, and should be used instead of the shortcut methods. This message also applies to the other event shorthands, including: blur, focus, focusin, focusout, resize, scroll, dblclick, mousedown, mouseup, mousemove, mouseover, mouseout, mouseenter, mouseleave, change, select, submit, keydown, keypress, keyup, and contextmenu.
     *
     * **Solution**: Instead of `.click(fn)` use `.on("click", fn)`. Instead of `.click()` use `.trigger("click")`.
     */
    focus<TData>(eventData: TData,
                 handler: JQuery.TypeEventHandler<TElement, TData, TElement, TElement, 'focus'>): this;
    /**
     * Bind an event handler to the "focus" JavaScript event, or trigger that event on an element.
     * @param handler A function to execute each time the event is triggered.
     * @see \`{@link https://api.jquery.com/focus/ }\`
     * @since 1.0
     * @deprecated ​ Deprecated since 3.3. Use \`{@link on }\` or \`{@link trigger }\`.
     *
     * **Cause**: The `.on()` and `.trigger()` methods can set an event handler or generate an event for any event type, and should be used instead of the shortcut methods. This message also applies to the other event shorthands, including: blur, focus, focusin, focusout, resize, scroll, dblclick, mousedown, mouseup, mousemove, mouseover, mouseout, mouseenter, mouseleave, change, select, submit, keydown, keypress, keyup, and contextmenu.
     *
     * **Solution**: Instead of `.click(fn)` use `.on("click", fn)`. Instead of `.click()` use `.trigger("click")`.
     * @example ​ ````Fire focus.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>focus demo</title>
  <style>
  span {
    display: none;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><input type="text"> <span>focus fire</span></p>
<p><input type="password"> <span>focus fire</span></p>
​
<script>
$( "input" ).focus(function() {
  $( this ).next( "span" ).css( "display", "inline" ).fadeOut( 1000 );
});
</script>
​
</body>
</html>
```
     * @example ​ ````To stop people from writing in text input boxes, try:
```javascript
$( "input[type=text]" ).focus(function() {
  $( this ).blur();
});
```
     * @example ​ ````To focus on a login input box with id &#39;login&#39; on page startup, try:
```javascript
$( document ).ready(function() {
  $( "#login" ).focus();
});
```
     */
    focus(handler?: JQuery.TypeEventHandler<TElement, null, TElement, TElement, 'focus'> |
                    false): this;
    /**
     * Bind an event handler to the "focusin" event.
     * @param eventData An object containing data that will be passed to the event handler.
     * @param handler A function to execute each time the event is triggered.
     * @see \`{@link https://api.jquery.com/focusin/ }\`
     * @since 1.4.3
     * @deprecated ​ Deprecated since 3.3. Use \`{@link on }\` or \`{@link trigger }\`.
     *
     * **Cause**: The `.on()` and `.trigger()` methods can set an event handler or generate an event for any event type, and should be used instead of the shortcut methods. This message also applies to the other event shorthands, including: blur, focus, focusin, focusout, resize, scroll, dblclick, mousedown, mouseup, mousemove, mouseover, mouseout, mouseenter, mouseleave, change, select, submit, keydown, keypress, keyup, and contextmenu.
     *
     * **Solution**: Instead of `.click(fn)` use `.on("click", fn)`. Instead of `.click()` use `.trigger("click")`.
     */
    focusin<TData>(eventData: TData,
                   handler: JQuery.TypeEventHandler<TElement, TData, TElement, TElement, 'focusin'>): this;
    /**
     * Bind an event handler to the "focusin" event.
     * @param handler A function to execute each time the event is triggered.
     * @see \`{@link https://api.jquery.com/focusin/ }\`
     * @since 1.4
     * @deprecated ​ Deprecated since 3.3. Use \`{@link on }\` or \`{@link trigger }\`.
     *
     * **Cause**: The `.on()` and `.trigger()` methods can set an event handler or generate an event for any event type, and should be used instead of the shortcut methods. This message also applies to the other event shorthands, including: blur, focus, focusin, focusout, resize, scroll, dblclick, mousedown, mouseup, mousemove, mouseover, mouseout, mouseenter, mouseleave, change, select, submit, keydown, keypress, keyup, and contextmenu.
     *
     * **Solution**: Instead of `.click(fn)` use `.on("click", fn)`. Instead of `.click()` use `.trigger("click")`.
     * @example ​ ````Watch for a focus to occur within the paragraphs on the page.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>focusin demo</title>
  <style>
  span {
    display: none;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><input type="text"> <span>focusin fire</span></p>
<p><input type="password"> <span>focusin fire</span></p>
​
<script>
$( "p" ).focusin(function() {
  $( this ).find( "span" ).css( "display", "inline" ).fadeOut( 1000 );
});
</script>
​
</body>
</html>
```
     */
    focusin(handler?: JQuery.TypeEventHandler<TElement, null, TElement, TElement, 'focusin'> |
                      false): this;
    /**
     * Bind an event handler to the "focusout" JavaScript event.
     * @param eventData An object containing data that will be passed to the event handler.
     * @param handler A function to execute each time the event is triggered.
     * @see \`{@link https://api.jquery.com/focusout/ }\`
     * @since 1.4.3
     * @deprecated ​ Deprecated since 3.3. Use \`{@link on }\` or \`{@link trigger }\`.
     *
     * **Cause**: The `.on()` and `.trigger()` methods can set an event handler or generate an event for any event type, and should be used instead of the shortcut methods. This message also applies to the other event shorthands, including: blur, focus, focusin, focusout, resize, scroll, dblclick, mousedown, mouseup, mousemove, mouseover, mouseout, mouseenter, mouseleave, change, select, submit, keydown, keypress, keyup, and contextmenu.
     *
     * **Solution**: Instead of `.click(fn)` use `.on("click", fn)`. Instead of `.click()` use `.trigger("click")`.
     */
    focusout<TData>(eventData: TData,
                    handler: JQuery.TypeEventHandler<TElement, TData, TElement, TElement, 'focusout'>): this;
    /**
     * Bind an event handler to the "focusout" JavaScript event.
     * @param handler A function to execute each time the event is triggered.
     * @see \`{@link https://api.jquery.com/focusout/ }\`
     * @since 1.4
     * @deprecated ​ Deprecated since 3.3. Use \`{@link on }\` or \`{@link trigger }\`.
     *
     * **Cause**: The `.on()` and `.trigger()` methods can set an event handler or generate an event for any event type, and should be used instead of the shortcut methods. This message also applies to the other event shorthands, including: blur, focus, focusin, focusout, resize, scroll, dblclick, mousedown, mouseup, mousemove, mouseover, mouseout, mouseenter, mouseleave, change, select, submit, keydown, keypress, keyup, and contextmenu.
     *
     * **Solution**: Instead of `.click(fn)` use `.on("click", fn)`. Instead of `.click()` use `.trigger("click")`.
     * @example ​ ````Watch for a loss of focus to occur inside paragraphs and note the difference between the focusout count and the blur count. (The blur count does not change because those events do not bubble.)
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>focusout demo</title>
  <style>
  .inputs {
    float: left;
    margin-right: 1em;
  }
  .inputs p {
    margin-top: 0;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<div class="inputs">
  <p>
    <input type="text"><br>
    <input type="text">
  </p>
  <p>
    <input type="password">
  </p>
</div>
<div id="focus-count">focusout fire</div>
<div id="blur-count">blur fire</div>
​
<script>
var focus = 0,
  blur = 0;
$( "p" )
  .focusout(function() {
    focus++;
    $( "#focus-count" ).text( "focusout fired: " + focus + "x" );
  })
  .blur(function() {
    blur++;
    $( "#blur-count" ).text( "blur fired: " + blur + "x" );
  });
</script>
​
</body>
</html>
```
     */
    focusout(handler?: JQuery.TypeEventHandler<TElement, null, TElement, TElement, 'focusout'> |
                       false): this;
    /**
     * Retrieve one of the elements matched by the jQuery object.
     * @param index A zero-based integer indicating which element to retrieve.
     * @see \`{@link https://api.jquery.com/get/ }\`
     * @since 1.0
     * @example ​ ````Display the tag name of the click element.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>get demo</title>
  <style>
  span {
    color: red;
  }
  div {
    background: yellow;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<span>&nbsp;</span>
<p>In this paragraph is an <span>important</span> section</p>
<div><input type="text"></div>
​
<script>
$( "*", document.body ).click(function( event ) {
  event.stopPropagation();
  var domElement = $( this ).get( 0 );
  $( "span:first" ).text( "Clicked on - " + domElement.nodeName );
});
</script>
​
</body>
</html>
```
     */
    get(index: number): TElement;
    /**
     * Retrieve the elements matched by the jQuery object.
     * @see \`{@link https://api.jquery.com/get/ }\`
     * @since 1.0
     * @example ​ ````Select all divs in the document and return the DOM Elements as an Array; then use the built-in reverse() method to reverse that array.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>get demo</title>
  <style>
  span {
    color: red;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
Reversed - <span></span>
​
<div>One</div>
<div>Two</div>
<div>Three</div>
​
<script>
function display( divs ) {
  var a = [];
  for ( var i = 0; i < divs.length; i++ ) {
    a.push( divs[ i ].innerHTML );
  }
  $( "span" ).text( a.join(" ") );
}
display( $( "div" ).get().reverse() );
</script>
​
</body>
</html>
```
     */
    get(): TElement[];
    /**
     * Reduce the set of matched elements to those that have a descendant that matches the selector or DOM element.
     * @param selector_contained _&#x40;param_ `selector_contained`
     * <br>
     * * `selector` — A string containing a selector expression to match elements against. <br>
     * * `contained` — A DOM element to match elements against.
     * @see \`{@link https://api.jquery.com/has/ }\`
     * @since 1.4
     * @example ​ ````Check if an element is inside another.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>has demo</title>
  <style>
  .full {
    border: 1px solid red;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<ul><li>Does the UL contain an LI?</li></ul>
​
<script>
$( "ul" ).append( "<li>" +
  ( $( "ul" ).has( "li" ).length ? "Yes" : "No" ) +
  "</li>" );
$( "ul" ).has( "li" ).addClass( "full" );
</script>
​
</body>
</html>
```
     */
    has(selector_contained: string | Element): this;
    /**
     * Determine whether any of the matched elements are assigned the given class.
     * @param className The class name to search for.
     * @see \`{@link https://api.jquery.com/hasClass/ }\`
     * @since 1.2
     * @example ​ ````Looks for the paragraph that contains &#39;selected&#39; as a class.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>hasClass demo</title>
  <style>
  p {
    margin: 8px;
    font-size: 16px;
  }
  .selected {
    color: red;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p>This paragraph is black and is the first paragraph.</p>
<p class="selected">This paragraph is red and is the second paragraph.</p>
<div id="result1">First paragraph has selected class: </div>
<div id="result2">Second paragraph has selected class: </div>
<div id="result3">At least one paragraph has selected class: </div>
​
<script>
$( "#result1" ).append( $( "p:first" ).hasClass( "selected" ).toString() );
$( "#result2" ).append( $( "p:last" ).hasClass( "selected" ).toString() );
$( "#result3" ).append( $( "p" ).hasClass( "selected" ).toString() ) ;
</script>
​
</body>
</html>
```
     */
    hasClass(className: string): boolean;
    /**
     * Set the CSS height of every matched element.
     * @param value_function _&#x40;param_ `value_function`
     * <br>
     * * `value` — An integer representing the number of pixels, or an integer with an optional unit of measure
     *             appended (as a string). <br>
     * * `function` — A function returning the height to set. Receives the index position of the element in the set and
     *                the old height as arguments. Within the function, `this` refers to the current element in the set.
     * @see \`{@link https://api.jquery.com/height/ }\`
     * @since 1.0
     * @since 1.4.1
     * @example ​ ````To set the height of each div on click to 30px plus a color change.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>height demo</title>
  <style>
  div {
    width: 50px;
    height: 70px;
    float: left;
    margin: 5px;
    background: rgb(255,140,0);
    cursor: pointer;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<div></div>
<div></div>
<div></div>
<div></div>
<div></div>
​
<script>
$( "div" ).one( "click", function() {
  $( this ).height( 30 ).css({
    cursor: "auto",
    backgroundColor: "green"
  });
});
</script>
​
</body>
</html>
```
     */
    height(value_function: string | number | ((this: TElement, index: number, height: number) => string | number)): this;
    /**
     * Get the current computed height for the first element in the set of matched elements.
     * @see \`{@link https://api.jquery.com/height/ }\`
     * @since 1.0
     * @example ​ ````Show various heights.  Note the values are from the iframe so might be smaller than you expected.  The yellow highlight shows the iframe body.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>height demo</title>
  <style>
  body {
    background: yellow;
  }
  button {
    font-size: 12px;
    margin: 2px;
  }
  p {
    width: 150px;
    border: 1px red solid;
  }
  div {
    color: red;
    font-weight: bold;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<button id="getp">Get Paragraph Height</button>
<button id="getd">Get Document Height</button>
<button id="getw">Get Window Height</button>
​
<div>&nbsp;</div>
<p>
  Sample paragraph to test height
</p>
​
<script>
function showHeight( element, height ) {
  $( "div" ).text( "The height for the " + element + " is " + height + "px." );
}
$( "#getp" ).click(function() {
  showHeight( "paragraph", $( "p" ).height() );
});
$( "#getd" ).click(function() {
  showHeight( "document", $( document ).height() );
});
$( "#getw" ).click(function() {
  showHeight( "window", $( window ).height() );
});
</script>
​
</body>
</html>
```
     */
    height(): number | undefined;
    /**
     * Hide the matched elements.
     * @param duration A string or number determining how long the animation will run.
     * @param easing A string indicating which easing function to use for the transition.
     * @param complete A function to call once the animation is complete, called once per matched element.
     * @see \`{@link https://api.jquery.com/hide/ }\`
     * @since 1.4.3
     */
    hide(duration: JQuery.Duration, easing: string, complete: (this: TElement) => void): this;
    /**
     * Hide the matched elements.
     * @param duration A string or number determining how long the animation will run.
     * @param easing_complete _&#x40;param_ `easing_complete`
     * <br>
     * * `easing` — A string indicating which easing function to use for the transition. <br>
     * * `complete` — A function to call once the animation is complete, called once per matched element.
     * @see \`{@link https://api.jquery.com/hide/ }\`
     * @since 1.0
     * @since 1.4.3
     * @example ​ ````Animates all spans (words in this case) to hide fastly, completing each animation within 200 milliseconds. Once each animation is done, it starts the next one.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>hide demo</title>
  <style>
  span {
    background: #def3ca;
    padding: 3px;
    float: left;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<button id="hider">Hide</button>
<button id="shower">Show</button>
<div>
  <span>Once</span> <span>upon</span> <span>a</span>
  <span>time</span> <span>there</span> <span>were</span>
  <span>three</span> <span>programmers...</span>
</div>
​
<script>
$( "#hider" ).click(function() {
  $( "span:last-child" ).hide( "fast", function() {
    // Use arguments.callee so we don't need a named function
    $( this ).prev().hide( "fast", arguments.callee );
  });
});
$( "#shower" ).click(function() {
  $( "span" ).show( 2000 );
});
</script>
​
</body>
</html>
```
     * @example ​ ````Hides the divs when clicked over 2 seconds, then removes the div element when its hidden.  Try clicking on more than one box at a time.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>hide demo</title>
  <style>
  div {
    background: #ece023;
    width: 30px;
    height: 40px;
    margin: 2px;
    float: left;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<div></div>
​
<script>
for ( var i = 0; i < 5; i++ ) {
  $( "<div>" ).appendTo( document.body );
}
$( "div" ).click(function() {
  $( this ).hide( 2000, function() {
    $( this ).remove();
  });
});
</script>
​
</body>
</html>
```
     */
    hide(duration: JQuery.Duration, easing_complete: string | ((this: TElement) => void)): this;
    /**
     * Hide the matched elements.
     * @param duration_complete_options _&#x40;param_ `duration_complete_options`
     * <br>
     * * `duration` — A string or number determining how long the animation will run. <br>
     * * `complete` — A function to call once the animation is complete, called once per matched element. <br>
     * * `options` — A map of additional options to pass to the method.
     * @see \`{@link https://api.jquery.com/hide/ }\`
     * @since 1.0
     * @example ​ ````Hides all paragraphs then the link on click.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>hide demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p>Hello</p>
<a href="#">Click to hide me too</a>
<p>Here is another paragraph</p>
​
<script>
$( "p" ).hide();
$( "a" ).click(function( event ) {
  event.preventDefault();
  $( this ).hide();
});
</script>
​
</body>
</html>
```
     * @example ​ ````Animates all shown paragraphs to hide slowly, completing the animation within 600 milliseconds.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>hide demo</title>
  <style>
  p {
    background: #dad;
    font-weight: bold;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<button>Hide 'em</button>
<p>Hiya</p>
<p>Such interesting text, eh?</p>
​
<script>
$( "button" ).click(function() {
  $( "p" ).hide( "slow" );
});
</script>
​
</body>
</html>
```
     */
    hide(duration_complete_options?: JQuery.Duration | ((this: TElement) => void) | JQuery.EffectsOptions<TElement>): this;
    /**
     * Bind two handlers to the matched elements, to be executed when the mouse pointer enters and leaves the elements.
     * @param handlerIn A function to execute when the mouse pointer enters the element.
     * @param handlerOut A function to execute when the mouse pointer leaves the element.
     * @see \`{@link https://api.jquery.com/hover/ }\`
     * @since 1.0
     * @deprecated ​ Deprecated.
     *
     * **Cause**: The `.hover()` method is a shorthand for the use of the `mouseover`/`mouseout` events. It is often a poor user interface choice because it does not allow for any small amounts of delay between when the mouse enters or exits an area and when the event fires. This can make it quite difficult to use with UI widgets such as drop-down menus. For more information on the problems of hovering, see the \`{@link http://cherne.net/brian/resources/jquery.hoverIntent.html hoverIntent plugin}\`.
     *
     * **Solution**: Review uses of `.hover()` to determine if they are appropriate, and consider use of plugins such as `hoverIntent` as an alternative. The direct replacement for `.hover(fn1, fn2)`, is `.on("mouseenter", fn1).on("mouseleave", fn2)`.
     * @example ​ ````To add a special style to list items that are being hovered over, try:
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>hover demo</title>
  <style>
  ul {
    margin-left: 20px;
    color: blue;
  }
  li {
    cursor: default;
  }
  span {
    color: red;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<ul>
  <li>Milk</li>
  <li>Bread</li>
  <li class="fade">Chips</li>
  <li class="fade">Socks</li>
</ul>
​
<script>
$( "li" ).hover(
  function() {
    $( this ).append( $( "<span> ***</span>" ) );
  }, function() {
    $( this ).find( "span:last" ).remove();
  }
);
​
$( "li.fade" ).hover(function() {
  $( this ).fadeOut( 100 );
  $( this ).fadeIn( 500 );
});
</script>
​
</body>
</html>
```
     * @example ​ ````To add a special style to table cells that are being hovered over, try:
```javascript
$( "td" ).hover(
  function() {
    $( this ).addClass( "hover" );
  }, function() {
    $( this ).removeClass( "hover" );
  }
);
```
     * @example ​ ````To unbind the above example use:
```javascript
$( "td" ).off( "mouseenter mouseleave" );
```
     */
    hover(handlerIn: JQuery.TypeEventHandler<TElement, null, TElement, TElement, 'mouseenter'> |
                     false,
          handlerOut: JQuery.TypeEventHandler<TElement, null, TElement, TElement, 'mouseleave'> |
                      false): this;
    /**
     * Bind a single handler to the matched elements, to be executed when the mouse pointer enters or leaves the elements.
     * @param handlerInOut A function to execute when the mouse pointer enters or leaves the element.
     * @see \`{@link https://api.jquery.com/hover/ }\`
     * @since 1.4
     * @deprecated ​ Deprecated.
     *
     * **Cause**: The `.hover()` method is a shorthand for the use of the `mouseover`/`mouseout` events. It is often a poor user interface choice because it does not allow for any small amounts of delay between when the mouse enters or exits an area and when the event fires. This can make it quite difficult to use with UI widgets such as drop-down menus. For more information on the problems of hovering, see the \`{@link http://cherne.net/brian/resources/jquery.hoverIntent.html hoverIntent plugin}\`.
     *
     * **Solution**: Review uses of `.hover()` to determine if they are appropriate, and consider use of plugins such as `hoverIntent` as an alternative. The direct replacement for `.hover(fn1, fn2)`, is `.on("mouseenter", fn1).on("mouseleave", fn2)`.
     * @example ​ ````Slide the next sibling LI up or down on hover, and toggle a class.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>hover demo</title>
  <style>
  ul {
    margin-left: 20px;
    color: blue;
  }
  li {
    cursor: default;
  }
  li.active {
    background: black;
    color: white;
  }
  span {
    color:red;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<ul>
  <li>Milk</li>
  <li>White</li>
  <li>Carrots</li>
  <li>Orange</li>
  <li>Broccoli</li>
  <li>Green</li>
</ul>
​
<script>
$( "li" )
  .filter( ":odd" )
    .hide()
  .end()
  .filter( ":even" )
    .hover(function() {
      $( this )
        .toggleClass( "active" )
        .next()
          .stop( true, true )
          .slideToggle();
    });
</script>
​
</body>
</html>
```
     */
    hover(handlerInOut: JQuery.TypeEventHandler<TElement, null, TElement, TElement, 'mouseenter' | 'mouseleave'> |
                        false): this;
    /**
     * Set the HTML contents of each element in the set of matched elements.
     * @param htmlString_function _&#x40;param_ `htmlString_function`
     * <br>
     * * `htmlString` — A string of HTML to set as the content of each matched element. <br>
     * * `function` — A function returning the HTML content to set. Receives the index position of the element in the set
     *                and the old HTML value as arguments. jQuery empties the element before calling the function; use the
     *                oldhtml argument to reference the previous content. Within the function, `this` refers to the current
     *                element in the set.
     * @see \`{@link https://api.jquery.com/html/ }\`
     * @since 1.0
     * @since 1.4
     * @example ​ ````Add some html to each div.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>html demo</title>
  <style>
  .red {
    color: red;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<span>Hello</span>
<div></div>
<div></div>
<div></div>
​
<script>
$( "div" ).html( "<span class='red'>Hello <b>Again</b></span>" );
</script>
​
</body>
</html>
```
     * @example ​ ````Add some html to each div then immediately do further manipulations to the inserted html.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>html demo</title>
  <style>
  div {
    color: blue;
    font-size: 18px;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<div></div>
<div></div>
<div></div>
​
<script>
$( "div" ).html( "<b>Wow!</b> Such excitement..." );
$( "div b" )
  .append( document.createTextNode( "!!!" ) )
  .css( "color", "red" );
</script>
​
</body>
</html>
```
     */
    html(htmlString_function: JQuery.htmlString |
                              JQuery.Node |
                              ((this: TElement, index: number, oldhtml: JQuery.htmlString) => JQuery.htmlString | JQuery.Node)): this;
    /**
     * Get the HTML contents of the first element in the set of matched elements.
     * @see \`{@link https://api.jquery.com/html/ }\`
     * @since 1.0
     * @example ​ ````Click a paragraph to convert it from html to text.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>html demo</title>
  <style>
  p {
    margin: 8px;
    font-size: 20px;
    color: blue;
    cursor: pointer;
  }
  b {
    text-decoration: underline;
  }
  button {
    cursor: pointer;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p>
  <b>Click</b> to change the <span id="tag">html</span>
</p>
<p>
  to a <span id="text">text</span> node.
</p>
<p>
  This <button name="nada">button</button> does nothing.
</p>
​
<script>
$( "p" ).click(function() {
  var htmlString = $( this ).html();
  $( this ).text( htmlString );
});
</script>
​
</body>
</html>
```
     */
    html(): string;
    /**
     * Search for a given element from among the matched elements.
     * @param selector_element _&#x40;param_ `selector_element`
     * <br>
     * * `selector` — A selector representing a jQuery collection in which to look for an element. <br>
     * * `element` — The DOM element or first element within the jQuery object to look for.
     * @see \`{@link https://api.jquery.com/index/ }\`
     * @since 1.0
     * @since 1.4
     * @example ​ ````On click, returns the index (zero-based) of that div in the page.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>index demo</title>
  <style>
  div {
    background: yellow;
    margin: 5px;
  }
  span {
    color: red;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<span>Click a div!</span>
<div>First div</div>
<div>Second div</div>
<div>Third div</div>
​
<script>
$( "div" ).click(function() {
  // `this` is the DOM element that was clicked
  var index = $( "div" ).index( this );
  $( "span" ).text( "That was div index #" + index );
});
</script>
​
</body>
</html>
```
     * @example ​ ````Returns the index for the element with ID bar.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>index demo</title>
  <style>
  div {
    font-weight: bold;
    color: #090;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<ul>
  <li id="foo">foo</li>
  <li id="bar">bar</li>
  <li id="baz">baz</li>
</ul>
<div></div>
​
<script>
var listItem = $( "#bar" );
$( "div" ).html( "Index: " + $( "li" ).index( listItem ) );
</script>
​
</body>
</html>
```
     * @example ​ ````Returns the index for the first item in the jQuery collection.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>index demo</title>
  <style>
  div {
    font-weight: bold;
    color: #090;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<ul>
  <li id="foo">foo</li>
  <li id="bar">bar</li>
  <li id="baz">baz</li>
</ul>
<div></div>
​
<script>
var listItems = $( "li:gt(0)" );
$( "div" ).html( "Index: " + $( "li" ).index( listItems ) );
</script>
​
</body>
</html>
```
     * @example ​ ````Returns the index for the element with ID bar in relation to all &lt;li&gt; elements.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>index demo</title>
  <style>
  div {
    font-weight: bold;
    color: #090;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<ul>
  <li id="foo">foo</li>
  <li id="bar">bar</li>
  <li id="baz">baz</li>
</ul>
<div></div>
​
<script>
$( "div" ).html( "Index: " +  $( "#bar" ).index( "li" ) );
</script>
​
</body>
</html>
```
     * @example ​ ````Returns the index for the element with ID bar in relation to its siblings.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>index demo</title>
  <style>
  div {
    font-weight: bold;
    color: #090;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<ul>
  <li id="foo">foo</li>
  <li id="bar">bar</li>
  <li id="baz">baz</li>
</ul>
<div></div>
​
<script>
var barIndex = $( "#bar" ).index();
$( "div" ).html( "Index: " +  barIndex );
</script>
​
</body>
</html>
```
     * @example ​ ````Returns -1, as there is no element with ID foobar.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>index demo</title>
  <style>
  div {
    font-weight: bold;
    color: #090;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<ul>
  <li id="foo">foo</li>
  <li id="bar">bar</li>
  <li id="baz">baz</li>
</ul>
<div></div>
​
<script>
var foobar = $( "li" ).index( $( "#foobar" ) );
$( "div" ).html( "Index: " + foobar );
</script>
​
</body>
</html>
```
     */
    index(selector_element?: JQuery.Selector | Element | JQuery): number;
    /**
     * Set the CSS inner height of each element in the set of matched elements.
     * @param value_function _&#x40;param_ `value_function`
     * <br>
     * * `value` — A number representing the number of pixels, or a number along with an optional unit of measure
     *             appended (as a string). <br>
     * * `function` — A function returning the inner height (including padding but not border) to set. Receives the index
     *                position of the element in the set and the old inner height as arguments. Within the function, `this`
     *                refers to the current element in the set.
     * @see \`{@link https://api.jquery.com/innerHeight/ }\`
     * @since 1.8.0
     * @example ​ ````Change the inner height of each div the first time it is clicked (and change its color).
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>innerHeight demo</title>
  <style>
div {
  width: 60px;
  padding: 10px;
  height: 70px;
  float: left;
  margin: 5px;
  background: red;
  cursor: pointer;
}
.mod {
  background: blue;
  cursor: default;
}
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<div>d</div>
<div>d</div>
<div>d</div>
<div>d</div>
<div>d</div>
​
<script>
var modHeight = 70;
$( "div" ).one( "click", function() {
  $( this ).innerHeight( modHeight ).addClass( "mod" );
  modHeight -= 8;
});
</script>
​
</body>
</html>
```
     */
    innerHeight(value_function: string | number | ((this: TElement, index: number, height: number) => string | number)): this;
    /**
     * Get the current computed height for the first element in the set of matched elements, including padding but not border.
     * @see \`{@link https://api.jquery.com/innerHeight/ }\`
     * @since 1.2.6
     * @example ​ ````Get the innerHeight of a paragraph.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>innerHeight demo</title>
  <style>
  p {
    margin: 10px;
    padding: 5px;
    border: 2px solid #666;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p>Hello</p>
<p></p>
​
<script>
var p = $( "p:first" );
$( "p:last" ).text( "innerHeight:" + p.innerHeight() );
</script>
​
</body>
</html>
```
     */
    innerHeight(): number | undefined;
    /**
     * Set the CSS inner width of each element in the set of matched elements.
     * @param value_function _&#x40;param_ `value_function`
     * <br>
     * * `value` — A number representing the number of pixels, or a number along with an optional unit of measure
     *             appended (as a string). <br>
     * * `function` — A function returning the inner width (including padding but not border) to set. Receives the index
     *                position of the element in the set and the old inner width as arguments. Within the function, `this`
     *                refers to the current element in the set.
     * @see \`{@link https://api.jquery.com/innerWidth/ }\`
     * @since 1.8.0
     * @example ​ ````Change the inner width of each div the first time it is clicked (and change its color).
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>innerWidth demo</title>
  <style>
div {
width: 60px;
padding: 10px;
height: 50px;
float: left;
margin: 5px;
background: red;
cursor: pointer;
}
.mod {
background: blue;
cursor: default;
}
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<div>d</div>
<div>d</div>
<div>d</div>
<div>d</div>
<div>d</div>
​
<script>
var modWidth = 60;
$( "div" ).one( "click", function() {
$( this ).innerWidth( modWidth ).addClass( "mod" );
modWidth -= 8;
});
</script>
​
</body>
</html>
```
     */
    innerWidth(value_function: string | number | ((this: TElement, index: number, width: number) => string | number)): this;
    /**
     * Get the current computed inner width for the first element in the set of matched elements, including padding but not border.
     * @see \`{@link https://api.jquery.com/innerWidth/ }\`
     * @since 1.2.6
     * @example ​ ````Get the innerWidth of a paragraph.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>innerWidth demo</title>
  <style>
  p {
    margin: 10px;
    padding: 5px;
    border: 2px solid #666;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p>Hello</p>
<p></p>
​
<script>
var p = $( "p:first" );
$( "p:last" ).text( "innerWidth:" + p.innerWidth() );
</script>
​
</body>
</html>
```
     */
    innerWidth(): number | undefined;
    /**
     * Insert every element in the set of matched elements after the target.
     * @param target A selector, element, array of elements, HTML string, or jQuery object; the matched set of elements
     *               will be inserted after the element(s) specified by this parameter.
     * @see \`{@link https://api.jquery.com/insertAfter/ }\`
     * @since 1.0
     * @example ​ ````Insert all paragraphs after an element with id of &quot;foo&quot;. Same as $( &quot;#foo&quot; ).after( &quot;p&quot; )
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>insertAfter demo</title>
  <style>
  #foo {
    background: yellow;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p> is what I said... </p>
<div id="foo">FOO!</div>
​
<script>
$( "p" ).insertAfter( "#foo" );
</script>
​
</body>
</html>
```
     */
    insertAfter(target: JQuery.Selector | JQuery.htmlString | JQuery.TypeOrArray<Node> | JQuery<Node>): this;
    /**
     * Insert every element in the set of matched elements before the target.
     * @param target A selector, element, array of elements, HTML string, or jQuery object; the matched set of elements
     *               will be inserted before the element(s) specified by this parameter.
     * @see \`{@link https://api.jquery.com/insertBefore/ }\`
     * @since 1.0
     * @example ​ ````Insert all paragraphs before an element with id of &quot;foo&quot;. Same as $( &quot;#foo&quot; ).before( &quot;p&quot; )
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>insertBefore demo</title>
  <style>
  #foo {
    background: yellow;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<div id="foo">FOO!</div>
<p>I would like to say: </p>
​
<script>
$( "p" ).insertBefore( "#foo" );
</script>
​
</body>
</html>
```
     */
    insertBefore(target: JQuery.Selector | JQuery.htmlString | JQuery.TypeOrArray<Node> | JQuery<Node>): this;
    /**
     * Check the current matched set of elements against a selector, element, or jQuery object and return true if at least one of these elements matches the given arguments.
     * @param selector_function_selection_elements _&#x40;param_ `selector_function_selection_elements`
     * <br>
     * * `selector` — A string containing a selector expression to match elements against. <br>
     * * `function` — A function used as a test for every element in the set. It accepts two arguments, `index`, which is
     *                the element's index in the jQuery collection, and `element`, which is the DOM element. Within the
     *                function, `this` refers to the current DOM element. <br>
     * * `selection` — An existing jQuery object to match the current set of elements against. <br>
     * * `elements` — One or more elements to match the current set of elements against.
     * @see \`{@link https://api.jquery.com/is/ }\`
     * @since 1.0
     * @since 1.6
     * @example ​ ````Shows a few ways is() can be used inside an event handler.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>is demo</title>
  <style>
  div {
    width: 60px;
    height: 60px;
    margin: 5px;
    float: left;
    border: 4px outset;
    background: green;
    text-align: center;
    font-weight: bolder;
    cursor: pointer;
  }
  .blue {
    background: blue;
  }
  .red {
    background: red;
  }
  span {
    color: white;
    font-size: 16px;
  }
  p {
    color: red;
    font-weight: bolder;
    background: yellow;
    margin: 3px;
    clear: left;
    display: none;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<div></div>
<div class="blue"></div>
<div></div>
<div class="red"></div>
<div><br/><span>Peter</span></div>
<div class="blue"></div>
<p>&nbsp;</p>
​
<script>
$( "div" ).one( "click", function() {
  if ( $( this ).is( ":first-child" ) ) {
    $( "p" ).text( "It's the first div." );
  } else if ( $( this ).is( ".blue,.red" ) ) {
    $( "p" ).text( "It's a blue or red div." );
  } else if ( $( this ).is( ":contains('Peter')" ) ) {
    $( "p" ).text( "It's Peter!" );
  } else {
    $( "p" ).html( "It's nothing <em>special</em>." );
  }
  $( "p" ).hide().slideDown( "slow" );
  $( this ).css({
    "border-style": "inset",
    cursor: "default"
  });
});
</script>
​
</body>
</html>
```
     * @example ​ ````Returns true, because the parent of the input is a form element.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>is demo</title>
  <style>
  div {
    color: red;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<form>
  <input type="checkbox">
</form>
<div></div>
​
<script>
var isFormParent = $( "input[type='checkbox']" ).parent().is( "form" );
$( "div" ).text( "isFormParent = " + isFormParent );
</script>
​
</body>
</html>
```
     * @example ​ ````Returns false, because the parent of the input is a p element.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>is demo</title>
  <style>
  div {
    color: red;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<form>
  <p><input type="checkbox"></p>
</form>
<div></div>
​
<script>
var isFormParent = $( "input[type='checkbox']" ).parent().is( "form" );
$( "div" ).text( "isFormParent = " + isFormParent );
</script>
​
</body>
</html>
```
     * @example ​ ````Checks against an existing collection of alternating list elements. Blue, alternating list elements slide up while others turn red.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>is demo</title>
  <style>
  li {
    cursor: pointer;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<ul id="browsers">
  <li>Chrome</li>
  <li>Safari</li>
  <li>Firefox</li>
  <li>Opera</li>
</ul>
​
<script>
var alt = $( "#browsers li:nth-child(2n)" ).css( "background", "#0ff" );
$( "li" ).click(function() {
  var li = $( this );
  if ( li.is( alt ) ) {
    li.slideUp();
  } else {
    li.css( "background", "red" );
  }
});
</script>
​
</body>
</html>
```
     * @example ​ ````An alternate way to achieve the above example using an element rather than a jQuery object. Checks against an existing collection of alternating list elements. Blue, alternating list elements slide up while others turn red.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>is demo</title>
  <style>
  li {
    cursor: pointer;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<ul id="browsers">
  <li>Chrome</li>
  <li>Safari</li>
  <li>Firefox</li>
  <li>Opera</li>
</ul>
​
<script>
var alt = $( "#browsers li:nth-child(2n)" ).css( "background", "#0ff" );
$( "li" ).click(function() {
  if ( alt.is( this ) ) {
    $( this ).slideUp();
  } else {
    $( this ).css( "background", "red" );
  }
});
</script>
​
</body>
</html>
```
     */
    is(selector_function_selection_elements: JQuery.Selector | JQuery.TypeOrArray<Element> | JQuery | ((this: TElement, index: number, element: TElement) => boolean)): boolean;
    /**
     * Bind an event handler to the "keydown" JavaScript event, or trigger that event on an element.
     * @param eventData An object containing data that will be passed to the event handler.
     * @param handler A function to execute each time the event is triggered.
     * @see \`{@link https://api.jquery.com/keydown/ }\`
     * @since 1.4.3
     * @deprecated ​ Deprecated since 3.3. Use \`{@link on }\` or \`{@link trigger }\`.
     *
     * **Cause**: The `.on()` and `.trigger()` methods can set an event handler or generate an event for any event type, and should be used instead of the shortcut methods. This message also applies to the other event shorthands, including: blur, focus, focusin, focusout, resize, scroll, dblclick, mousedown, mouseup, mousemove, mouseover, mouseout, mouseenter, mouseleave, change, select, submit, keydown, keypress, keyup, and contextmenu.
     *
     * **Solution**: Instead of `.click(fn)` use `.on("click", fn)`. Instead of `.click()` use `.trigger("click")`.
     */
    keydown<TData>(eventData: TData,
                   handler: JQuery.TypeEventHandler<TElement, TData, TElement, TElement, 'keydown'>): this;
    /**
     * Bind an event handler to the "keydown" JavaScript event, or trigger that event on an element.
     * @param handler A function to execute each time the event is triggered.
     * @see \`{@link https://api.jquery.com/keydown/ }\`
     * @since 1.0
     * @deprecated ​ Deprecated since 3.3. Use \`{@link on }\` or \`{@link trigger }\`.
     *
     * **Cause**: The `.on()` and `.trigger()` methods can set an event handler or generate an event for any event type, and should be used instead of the shortcut methods. This message also applies to the other event shorthands, including: blur, focus, focusin, focusout, resize, scroll, dblclick, mousedown, mouseup, mousemove, mouseover, mouseout, mouseenter, mouseleave, change, select, submit, keydown, keypress, keyup, and contextmenu.
     *
     * **Solution**: Instead of `.click(fn)` use `.on("click", fn)`. Instead of `.click()` use `.trigger("click")`.
     * @example ​ ````Show the event object for the keydown handler when a key is pressed in the input.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>keydown demo</title>
  <style>
  fieldset {
    margin-bottom: 1em;
  }
  input {
    display: block;
    margin-bottom: .25em;
  }
  #print-output {
    width: 100%;
  }
  .print-output-line {
    white-space: pre;
    padding: 5px;
    font-family: monaco, monospace;
    font-size: .7em;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<form>
  <fieldset>
    <label for="target">Type Something:</label>
    <input id="target" type="text">
  </fieldset>
</form>
<button id="other">
  Trigger the handler
</button>
<script type="text/javascript" src="/resources/events.js"></script>
​
<script>
var xTriggered = 0;
$( "#target" ).keydown(function( event ) {
  if ( event.which == 13 ) {
   event.preventDefault();
  }
  xTriggered++;
  var msg = "Handler for .keydown() called " + xTriggered + " time(s).";
  $.print( msg, "html" );
  $.print( event );
});
​
$( "#other" ).click(function() {
  $( "#target" ).keydown();
});
</script>
​
</body>
</html>
```
     */
    keydown(handler?: JQuery.TypeEventHandler<TElement, null, TElement, TElement, 'keydown'> |
                      false): this;
    /**
     * Bind an event handler to the "keypress" JavaScript event, or trigger that event on an element.
     * @param eventData An object containing data that will be passed to the event handler.
     * @param handler A function to execute each time the event is triggered.
     * @see \`{@link https://api.jquery.com/keypress/ }\`
     * @since 1.4.3
     * @deprecated ​ Deprecated since 3.3. Use \`{@link on }\` or \`{@link trigger }\`.
     *
     * **Cause**: The `.on()` and `.trigger()` methods can set an event handler or generate an event for any event type, and should be used instead of the shortcut methods. This message also applies to the other event shorthands, including: blur, focus, focusin, focusout, resize, scroll, dblclick, mousedown, mouseup, mousemove, mouseover, mouseout, mouseenter, mouseleave, change, select, submit, keydown, keypress, keyup, and contextmenu.
     *
     * **Solution**: Instead of `.click(fn)` use `.on("click", fn)`. Instead of `.click()` use `.trigger("click")`.
     */
    keypress<TData>(eventData: TData,
                    handler: JQuery.TypeEventHandler<TElement, TData, TElement, TElement, 'keypress'>): this;
    /**
     * Bind an event handler to the "keypress" JavaScript event, or trigger that event on an element.
     * @param handler A function to execute each time the event is triggered.
     * @see \`{@link https://api.jquery.com/keypress/ }\`
     * @since 1.0
     * @deprecated ​ Deprecated since 3.3. Use \`{@link on }\` or \`{@link trigger }\`.
     *
     * **Cause**: The `.on()` and `.trigger()` methods can set an event handler or generate an event for any event type, and should be used instead of the shortcut methods. This message also applies to the other event shorthands, including: blur, focus, focusin, focusout, resize, scroll, dblclick, mousedown, mouseup, mousemove, mouseover, mouseout, mouseenter, mouseleave, change, select, submit, keydown, keypress, keyup, and contextmenu.
     *
     * **Solution**: Instead of `.click(fn)` use `.on("click", fn)`. Instead of `.click()` use `.trigger("click")`.
     * @example ​ ````Show the event object when a key is pressed in the input. Note: This demo relies on a simple $.print() plugin (https://api.jquery.com/resources/events.js) for the event object&#39;s output.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>keypress demo</title>
  <style>
  fieldset {
    margin-bottom: 1em;
  }
  input {
    display: block;
    margin-bottom: .25em;
  }
  #print-output {
    width: 100%;
  }
  .print-output-line {
    white-space: pre;
    padding: 5px;
    font-family: monaco, monospace;
    font-size: .7em;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<form>
  <fieldset>
    <label for="target">Type Something:</label>
    <input id="target" type="text">
  </fieldset>
</form>
<button id="other">
  Trigger the handler
</button>
<script src="/resources/events.js"></script>
​
<script>
var xTriggered = 0;
$( "#target" ).keypress(function( event ) {
  if ( event.which == 13 ) {
     event.preventDefault();
  }
  xTriggered++;
  var msg = "Handler for .keypress() called " + xTriggered + " time(s).";
  $.print( msg, "html" );
  $.print( event );
});
​
$( "#other" ).click(function() {
  $( "#target" ).keypress();
});
</script>
​
</body>
</html>
```
     */
    keypress(handler?: JQuery.TypeEventHandler<TElement, null, TElement, TElement, 'keypress'> |
                       false): this;
    /**
     * Bind an event handler to the "keyup" JavaScript event, or trigger that event on an element.
     * @param eventData An object containing data that will be passed to the event handler.
     * @param handler A function to execute each time the event is triggered.
     * @see \`{@link https://api.jquery.com/keyup/ }\`
     * @since 1.4.3
     * @deprecated ​ Deprecated since 3.3. Use \`{@link on }\` or \`{@link trigger }\`.
     *
     * **Cause**: The `.on()` and `.trigger()` methods can set an event handler or generate an event for any event type, and should be used instead of the shortcut methods. This message also applies to the other event shorthands, including: blur, focus, focusin, focusout, resize, scroll, dblclick, mousedown, mouseup, mousemove, mouseover, mouseout, mouseenter, mouseleave, change, select, submit, keydown, keypress, keyup, and contextmenu.
     *
     * **Solution**: Instead of `.click(fn)` use `.on("click", fn)`. Instead of `.click()` use `.trigger("click")`.
     */
    keyup<TData>(eventData: TData,
                 handler: JQuery.TypeEventHandler<TElement, TData, TElement, TElement, 'keyup'>): this;
    /**
     * Bind an event handler to the "keyup" JavaScript event, or trigger that event on an element.
     * @param handler A function to execute each time the event is triggered.
     * @see \`{@link https://api.jquery.com/keyup/ }\`
     * @since 1.0
     * @deprecated ​ Deprecated since 3.3. Use \`{@link on }\` or \`{@link trigger }\`.
     *
     * **Cause**: The `.on()` and `.trigger()` methods can set an event handler or generate an event for any event type, and should be used instead of the shortcut methods. This message also applies to the other event shorthands, including: blur, focus, focusin, focusout, resize, scroll, dblclick, mousedown, mouseup, mousemove, mouseover, mouseout, mouseenter, mouseleave, change, select, submit, keydown, keypress, keyup, and contextmenu.
     *
     * **Solution**: Instead of `.click(fn)` use `.on("click", fn)`. Instead of `.click()` use `.trigger("click")`.
     * @example ​ ````Show the event object for the keyup handler (using a simple $.print plugin) when a key is released in the input.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>keyup demo</title>
  <style>
  fieldset {
    margin-bottom: 1em;
  }
  input {
    display: block;
    margin-bottom: .25em;
  }
  #print-output {
    width: 100%;
  }
  .print-output-line {
    white-space: pre;
    padding: 5px;
    font-family: monaco, monospace;
    font-size: .7em;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<form>
  <fieldset>
    <label for="target">Type Something:</label>
    <input id="target" type="text">
  </fieldset>
</form>
<button id="other">
  Trigger the handler
</button>
<script type="text/javascript" src="/resources/events.js"></script>
​
<script>
var xTriggered = 0;
$( "#target" ).keyup(function( event ) {
  xTriggered++;
  var msg = "Handler for .keyup() called " + xTriggered + " time(s).";
  $.print( msg, "html" );
  $.print( event );
}).keydown(function( event ) {
  if ( event.which == 13 ) {
    event.preventDefault();
  }
});
​
$( "#other").click(function() {
  $( "#target" ).keyup();
});
</script>
​
</body>
</html>
```
     */
    keyup(handler?: JQuery.TypeEventHandler<TElement, null, TElement, TElement, 'keyup'> |
                    false): this;
    /**
     * Reduce the set of matched elements to the final one in the set.
     * @see \`{@link https://api.jquery.com/last/ }\`
     * @since 1.4
     * @example ​ ````Highlight the last span in a paragraph.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>last demo</title>
  <style>
  .highlight {
    background-color: yellow;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><span>Look:</span> <span>This is some text in a paragraph.</span> <span>This is a note about it.</span></p>
​
<script>
$( "p span" ).last().addClass( "highlight" );
</script>
​
</body>
</html>
```
     */
    last(): this;
    /**
     * Load data from the server and place the returned HTML into the matched element.
     * @param url A string containing the URL to which the request is sent.
     * @param data A plain object or string that is sent to the server with the request.
     * @param complete A callback function that is executed when the request completes.
     * @see \`{@link https://api.jquery.com/load/ }\`
     * @since 1.0
     * @example ​ ````Same as above, but will POST the additional parameters to the server and a callback that is executed when the server is finished responding.
```javascript
$( "#feeds" ).load( "feeds.php", { limit: 25 }, function() {
  alert( "The last 25 entries in the feed have been loaded" );
});
```
     */
    load(url: string,
         data: string | JQuery.PlainObject,
         complete: (this: TElement, responseText: string, textStatus: JQuery.Ajax.TextStatus, jqXHR: JQuery.jqXHR) => void): this;
    /**
     * Load data from the server and place the returned HTML into the matched element.
     * @param url A string containing the URL to which the request is sent.
     * @param complete_data _&#x40;param_ `complete_data`
     * <br>
     * * `complete` — A callback function that is executed when the request completes. <br>
     * * `data` — A plain object or string that is sent to the server with the request.
     * @see \`{@link https://api.jquery.com/load/ }\`
     * @since 1.0
     * @example ​ ````Load another page&#39;s list items into an ordered list.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>load demo</title>
  <style>
  body {
    font-size: 12px;
    font-family: Arial;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<b>Projects:</b>
<ol id="new-projects"></ol>
​
<script>
$( "#new-projects" ).load( "/resources/load.html #projects li" );
</script>
​
</body>
</html>
```
     * @example ​ ````Display a notice if the Ajax request encounters an error.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>load demo</title>
  <style>
  body {
    font-size: 12px;
    font-family: Arial;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<b>Successful Response (should be blank):</b>
<div id="success"></div>
<b>Error Response:</b>
<div id="error"></div>
​
<script>
$( "#success" ).load( "/not-here.php", function( response, status, xhr ) {
  if ( status == "error" ) {
    var msg = "Sorry but there was an error: ";
    $( "#error" ).html( msg + xhr.status + " " + xhr.statusText );
  }
});
</script>
​
</body>
</html>
```
     * @example ​ ````Load the feeds.html file into the div with the ID of feeds.
```javascript
$( "#feeds" ).load( "feeds.html" );
```
     * @example ​ ````pass arrays of data to the server.
```javascript
$( "#objectID" ).load( "test.php", { "choices[]": [ "Jon", "Susan" ] } );
```
     */
    load(url: string,
         complete_data?: ((this: TElement, responseText: string, textStatus: JQuery.Ajax.TextStatus, jqXHR: JQuery.jqXHR) => void) | string | JQuery.PlainObject): this;
    /**
     * Pass each element in the current matched set through a function, producing a new jQuery object containing the return values.
     * @param callback A function object that will be invoked for each element in the current set.
     * @see \`{@link https://api.jquery.com/map/ }\`
     * @since 1.2
     * @example ​ ````Build a list of all the values within a form.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>map demo</title>
  <style>
  p {
    color: red;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><b>Values: </b></p>
<form>
  <input type="text" name="name" value="John">
  <input type="text" name="password" value="password">
  <input type="text" name="url" value="https://johnresig.com/">
</form>
​
<script>
$( "p" )
  .append( $( "input" ).map(function() {
    return $( this ).val();
  })
  .get()
  .join( ", " ) );
</script>
​
</body>
</html>
```
     * @example ​ ````A contrived example to show some functionality.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>map demo</title>
  <style>
  body {
    font-size: 16px;
  }
  ul {
    float: left;
    margin: 0 30px;
    color: blue;
  }
  #results {
    color: red;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<ul>
  <li>First</li>
  <li>Second</li>
  <li>Third</li>
  <li>Fourth</li>
  <li>Fifth</li>
</ul>
<ul id="results">
</ul>
​
<script>
var mappedItems = $( "li" ).map(function( index ) {
  var replacement = $( "<li>" ).text( $( this ).text() ).get( 0 );
  if ( index === 0 ) {
​
    // Make the first item all caps
    $( replacement ).text( $( replacement ).text().toUpperCase() );
  } else if ( index === 1 || index === 3 ) {
​
    // Delete the second and fourth items
    replacement = null;
  } else if ( index === 2 ) {
​
    // Make two of the third item and add some text
    replacement = [ replacement, $( "<li>" ).get( 0 ) ];
    $( replacement[ 0 ] ).append( "<b> - A</b>" );
    $( replacement[ 1 ] ).append( "Extra <b> - B</b>" );
  }
​
  // Replacement will be a dom element, null,
  // or an array of dom elements
  return replacement;
});
$( "#results" ).append( mappedItems );
</script>
​
</body>
</html>
```
     * @example ​ ````Equalize the heights of the divs.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>map demo</title>
  <style>
  div {
    width: 40px;
    float: left;
  }
  input {
    clear: left;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<input type="button" value="equalize div heights">
<div style="background: red; height: 40px; "></div>
<div style="background: green; height: 70px;"></div>
<div style="background: blue; height: 50px; "></div>
​
<script>
$.fn.equalizeHeights = function() {
  var maxHeight = this.map(function( i, e ) {
    return $( e ).height();
  }).get();
  return this.height( Math.max.apply( this, maxHeight ) );
};
​
$( "input" ).click(function() {
  $( "div" ).equalizeHeights();
});
</script>
​
</body>
</html>
```
     */
    map<TReturn>(callback: (this: TElement, index: number, domElement: TElement) => JQuery.TypeOrArray<TReturn> | null | undefined): JQuery<TReturn>;
    /**
     * Bind an event handler to the "mousedown" JavaScript event, or trigger that event on an element.
     * @param eventData An object containing data that will be passed to the event handler.
     * @param handler A function to execute each time the event is triggered.
     * @see \`{@link https://api.jquery.com/mousedown/ }\`
     * @since 1.4.3
     * @deprecated ​ Deprecated since 3.3. Use \`{@link on }\` or \`{@link trigger }\`.
     *
     * **Cause**: The `.on()` and `.trigger()` methods can set an event handler or generate an event for any event type, and should be used instead of the shortcut methods. This message also applies to the other event shorthands, including: blur, focus, focusin, focusout, resize, scroll, dblclick, mousedown, mouseup, mousemove, mouseover, mouseout, mouseenter, mouseleave, change, select, submit, keydown, keypress, keyup, and contextmenu.
     *
     * **Solution**: Instead of `.click(fn)` use `.on("click", fn)`. Instead of `.click()` use `.trigger("click")`.
     */
    mousedown<TData>(eventData: TData,
                     handler: JQuery.TypeEventHandler<TElement, TData, TElement, TElement, 'mousedown'>): this;
    /**
     * Bind an event handler to the "mousedown" JavaScript event, or trigger that event on an element.
     * @param handler A function to execute each time the event is triggered.
     * @see \`{@link https://api.jquery.com/mousedown/ }\`
     * @since 1.0
     * @deprecated ​ Deprecated since 3.3. Use \`{@link on }\` or \`{@link trigger }\`.
     *
     * **Cause**: The `.on()` and `.trigger()` methods can set an event handler or generate an event for any event type, and should be used instead of the shortcut methods. This message also applies to the other event shorthands, including: blur, focus, focusin, focusout, resize, scroll, dblclick, mousedown, mouseup, mousemove, mouseover, mouseout, mouseenter, mouseleave, change, select, submit, keydown, keypress, keyup, and contextmenu.
     *
     * **Solution**: Instead of `.click(fn)` use `.on("click", fn)`. Instead of `.click()` use `.trigger("click")`.
     * @example ​ ````Show texts when mouseup and mousedown event triggering.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>mousedown demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p>Press mouse and release here.</p>
​
<script>
$( "p" )
  .mouseup(function() {
    $( this ).append( "<span style='color:#f00;'>Mouse up.</span>" );
  })
  .mousedown(function() {
    $( this ).append( "<span style='color:#00f;'>Mouse down.</span>" );
  });
</script>
​
</body>
</html>
```
     */
    mousedown(handler?: JQuery.TypeEventHandler<TElement, null, TElement, TElement, 'mousedown'> |
                        false): this;
    /**
     * Bind an event handler to be fired when the mouse enters an element, or trigger that handler on an element.
     * @param eventData An object containing data that will be passed to the event handler.
     * @param handler A function to execute each time the event is triggered.
     * @see \`{@link https://api.jquery.com/mouseenter/ }\`
     * @since 1.4.3
     * @deprecated ​ Deprecated since 3.3. Use \`{@link on }\` or \`{@link trigger }\`.
     *
     * **Cause**: The `.on()` and `.trigger()` methods can set an event handler or generate an event for any event type, and should be used instead of the shortcut methods. This message also applies to the other event shorthands, including: blur, focus, focusin, focusout, resize, scroll, dblclick, mousedown, mouseup, mousemove, mouseover, mouseout, mouseenter, mouseleave, change, select, submit, keydown, keypress, keyup, and contextmenu.
     *
     * **Solution**: Instead of `.click(fn)` use `.on("click", fn)`. Instead of `.click()` use `.trigger("click")`.
     */
    mouseenter<TData>(eventData: TData,
                      handler: JQuery.TypeEventHandler<TElement, TData, TElement, TElement, 'mouseenter'>): this;
    /**
     * Bind an event handler to be fired when the mouse enters an element, or trigger that handler on an element.
     * @param handler A function to execute each time the event is triggered.
     * @see \`{@link https://api.jquery.com/mouseenter/ }\`
     * @since 1.0
     * @deprecated ​ Deprecated since 3.3. Use \`{@link on }\` or \`{@link trigger }\`.
     *
     * **Cause**: The `.on()` and `.trigger()` methods can set an event handler or generate an event for any event type, and should be used instead of the shortcut methods. This message also applies to the other event shorthands, including: blur, focus, focusin, focusout, resize, scroll, dblclick, mousedown, mouseup, mousemove, mouseover, mouseout, mouseenter, mouseleave, change, select, submit, keydown, keypress, keyup, and contextmenu.
     *
     * **Solution**: Instead of `.click(fn)` use `.on("click", fn)`. Instead of `.click()` use `.trigger("click")`.
     * @example ​ ````Show texts when mouseenter and mouseout event triggering.
    mouseover fires when the pointer moves into the child element as well, while mouseenter fires only when the pointer moves into the bound element.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>mouseenter demo</title>
  <style>
  div.out {
    width: 40%;
    height: 120px;
    margin: 0 15px;
    background-color: #d6edfc;
    float: left;
  }
  div.in {
    width: 60%;
    height: 60%;
    background-color: #fc0;
    margin: 10px auto;
  }
  p {
    line-height: 1em;
    margin: 0;
    padding: 0;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<div class="out overout">
  <p>move your mouse</p>
  <div class="in overout"><p>move your mouse</p><p>0</p></div>
  <p>0</p>
</div>
​
<div class="out enterleave">
  <p>move your mouse</p>
  <div class="in enterleave"><p>move your mouse</p><p>0</p></div>
  <p>0</p>
</div>
​
<script>
var i = 0;
$( "div.overout" )
  .mouseover(function() {
    $( "p:first", this ).text( "mouse over" );
    $( "p:last", this ).text( ++i );
  })
  .mouseout(function() {
    $( "p:first", this ).text( "mouse out" );
  });
​
var n = 0;
$( "div.enterleave" )
  .mouseenter(function() {
    $( "p:first", this ).text( "mouse enter" );
    $( "p:last", this ).text( ++n );
  })
  .mouseleave(function() {
    $( "p:first", this ).text( "mouse leave" );
  });
</script>
​
</body>
</html>
```
     */
    mouseenter(handler?: JQuery.TypeEventHandler<TElement, null, TElement, TElement, 'mouseenter'> |
                         false): this;
    /**
     * Bind an event handler to be fired when the mouse leaves an element, or trigger that handler on an element.
     * @param eventData An object containing data that will be passed to the event handler.
     * @param handler A function to execute each time the event is triggered.
     * @see \`{@link https://api.jquery.com/mouseleave/ }\`
     * @since 1.4.3
     * @deprecated ​ Deprecated since 3.3. Use \`{@link on }\` or \`{@link trigger }\`.
     *
     * **Cause**: The `.on()` and `.trigger()` methods can set an event handler or generate an event for any event type, and should be used instead of the shortcut methods. This message also applies to the other event shorthands, including: blur, focus, focusin, focusout, resize, scroll, dblclick, mousedown, mouseup, mousemove, mouseover, mouseout, mouseenter, mouseleave, change, select, submit, keydown, keypress, keyup, and contextmenu.
     *
     * **Solution**: Instead of `.click(fn)` use `.on("click", fn)`. Instead of `.click()` use `.trigger("click")`.
     */
    mouseleave<TData>(eventData: TData,
                      handler: JQuery.TypeEventHandler<TElement, TData, TElement, TElement, 'mouseleave'>): this;
    /**
     * Bind an event handler to be fired when the mouse leaves an element, or trigger that handler on an element.
     * @param handler A function to execute each time the event is triggered.
     * @see \`{@link https://api.jquery.com/mouseleave/ }\`
     * @since 1.0
     * @deprecated ​ Deprecated since 3.3. Use \`{@link on }\` or \`{@link trigger }\`.
     *
     * **Cause**: The `.on()` and `.trigger()` methods can set an event handler or generate an event for any event type, and should be used instead of the shortcut methods. This message also applies to the other event shorthands, including: blur, focus, focusin, focusout, resize, scroll, dblclick, mousedown, mouseup, mousemove, mouseover, mouseout, mouseenter, mouseleave, change, select, submit, keydown, keypress, keyup, and contextmenu.
     *
     * **Solution**: Instead of `.click(fn)` use `.on("click", fn)`. Instead of `.click()` use `.trigger("click")`.
     * @example ​ ````Show number of times mouseout and mouseleave events are triggered. mouseout fires when the pointer moves out of child element as well, while mouseleave fires only when the pointer moves out of the bound element.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>mouseleave demo</title>
  <style>
  div.out {
    width: 40%;
    height: 120px;
    margin: 0 15px;
    background-color: #d6edfc;
    float: left;
  }
  div.in {
    width: 60%;
    height: 60%;
    background-color: #fc0;
    margin: 10px auto;
  }
  p {
    line-height: 1em;
    margin: 0;
    padding: 0;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<div class="out overout">
  <p>move your mouse</p>
  <div class="in overout"><p>move your mouse</p><p>0</p></div>
  <p>0</p>
</div>
<div class="out enterleave">
  <p>move your mouse</p>
  <div class="in enterleave"><p>move your mouse</p><p>0</p></div>
  <p>0</p>
</div>
​
<script>
var i = 0;
$( "div.overout" )
  .mouseover(function() {
    $( "p:first", this ).text( "mouse over" );
  })
  .mouseout(function() {
    $( "p:first", this ).text( "mouse out" );
    $( "p:last", this ).text( ++i );
  });
​
var n = 0;
$( "div.enterleave" )
  .mouseenter(function() {
    $( "p:first", this ).text( "mouse enter" );
  })
  .mouseleave(function() {
    $( "p:first", this ).text( "mouse leave" );
    $( "p:last", this ).text( ++n );
  });
</script>
​
</body>
</html>
```
     */
    mouseleave(handler?: JQuery.TypeEventHandler<TElement, null, TElement, TElement, 'mouseleave'> |
                         false): this;
    /**
     * Bind an event handler to the "mousemove" JavaScript event, or trigger that event on an element.
     * @param eventData An object containing data that will be passed to the event handler.
     * @param handler A function to execute each time the event is triggered.
     * @see \`{@link https://api.jquery.com/mousemove/ }\`
     * @since 1.4.3
     * @deprecated ​ Deprecated since 3.3. Use \`{@link on }\` or \`{@link trigger }\`.
     *
     * **Cause**: The `.on()` and `.trigger()` methods can set an event handler or generate an event for any event type, and should be used instead of the shortcut methods. This message also applies to the other event shorthands, including: blur, focus, focusin, focusout, resize, scroll, dblclick, mousedown, mouseup, mousemove, mouseover, mouseout, mouseenter, mouseleave, change, select, submit, keydown, keypress, keyup, and contextmenu.
     *
     * **Solution**: Instead of `.click(fn)` use `.on("click", fn)`. Instead of `.click()` use `.trigger("click")`.
     */
    mousemove<TData>(eventData: TData,
                     handler: JQuery.TypeEventHandler<TElement, TData, TElement, TElement, 'mousemove'>): this;
    /**
     * Bind an event handler to the "mousemove" JavaScript event, or trigger that event on an element.
     * @param handler A function to execute each time the event is triggered.
     * @see \`{@link https://api.jquery.com/mousemove/ }\`
     * @since 1.0
     * @deprecated ​ Deprecated since 3.3. Use \`{@link on }\` or \`{@link trigger }\`.
     *
     * **Cause**: The `.on()` and `.trigger()` methods can set an event handler or generate an event for any event type, and should be used instead of the shortcut methods. This message also applies to the other event shorthands, including: blur, focus, focusin, focusout, resize, scroll, dblclick, mousedown, mouseup, mousemove, mouseover, mouseout, mouseenter, mouseleave, change, select, submit, keydown, keypress, keyup, and contextmenu.
     *
     * **Solution**: Instead of `.click(fn)` use `.on("click", fn)`. Instead of `.click()` use `.trigger("click")`.
     * @example ​ ````Show the mouse coordinates when the mouse is moved over the yellow div.  Coordinates are relative to the window, which in this case is the iframe.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>mousemove demo</title>
  <style>
  div {
    width: 220px;
    height: 170px;
    margin: 10px 50px 10px 10px;
    background: yellow;
    border: 2px groove;
    float: right;
  }
  p {
    margin: 0;
    margin-left: 10px;
    color: red;
    width: 220px;
    height: 120px;
    padding-top: 70px;
    float: left;
    font-size: 14px;
  }
  span {
    display: block;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p>
  <span>Move the mouse over the div.</span>
  <span>&nbsp;</span>
</p>
<div></div>
​
<script>
$( "div" ).mousemove(function( event ) {
  var pageCoords = "( " + event.pageX + ", " + event.pageY + " )";
  var clientCoords = "( " + event.clientX + ", " + event.clientY + " )";
  $( "span:first" ).text( "( event.pageX, event.pageY ) : " + pageCoords );
  $( "span:last" ).text( "( event.clientX, event.clientY ) : " + clientCoords );
});
</script>
​
</body>
</html>
```
     */
    mousemove(handler?: JQuery.TypeEventHandler<TElement, null, TElement, TElement, 'mousemove'> |
                        false): this;
    /**
     * Bind an event handler to the "mouseout" JavaScript event, or trigger that event on an element.
     * @param eventData An object containing data that will be passed to the event handler.
     * @param handler A function to execute each time the event is triggered.
     * @see \`{@link https://api.jquery.com/mouseout/ }\`
     * @since 1.4.3
     * @deprecated ​ Deprecated since 3.3. Use \`{@link on }\` or \`{@link trigger }\`.
     *
     * **Cause**: The `.on()` and `.trigger()` methods can set an event handler or generate an event for any event type, and should be used instead of the shortcut methods. This message also applies to the other event shorthands, including: blur, focus, focusin, focusout, resize, scroll, dblclick, mousedown, mouseup, mousemove, mouseover, mouseout, mouseenter, mouseleave, change, select, submit, keydown, keypress, keyup, and contextmenu.
     *
     * **Solution**: Instead of `.click(fn)` use `.on("click", fn)`. Instead of `.click()` use `.trigger("click")`.
     */
    mouseout<TData>(eventData: TData,
                    handler: JQuery.TypeEventHandler<TElement, TData, TElement, TElement, 'mouseout'>): this;
    /**
     * Bind an event handler to the "mouseout" JavaScript event, or trigger that event on an element.
     * @param handler A function to execute each time the event is triggered.
     * @see \`{@link https://api.jquery.com/mouseout/ }\`
     * @since 1.0
     * @deprecated ​ Deprecated since 3.3. Use \`{@link on }\` or \`{@link trigger }\`.
     *
     * **Cause**: The `.on()` and `.trigger()` methods can set an event handler or generate an event for any event type, and should be used instead of the shortcut methods. This message also applies to the other event shorthands, including: blur, focus, focusin, focusout, resize, scroll, dblclick, mousedown, mouseup, mousemove, mouseover, mouseout, mouseenter, mouseleave, change, select, submit, keydown, keypress, keyup, and contextmenu.
     *
     * **Solution**: Instead of `.click(fn)` use `.on("click", fn)`. Instead of `.click()` use `.trigger("click")`.
     * @example ​ ````Show the number of times mouseout and mouseleave events are triggered.
  mouseout fires when the pointer moves out of the child element as well, while mouseleave fires only when the pointer moves out of the bound element.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>mouseout demo</title>
  <style>
  div.out {
    width: 40%;
    height: 120px;
    margin: 0 15px;
    background-color: #d6edfc;
    float: left;
  }
  div.in {
    width: 60%;
    height: 60%;
    background-color: #fc0;
    margin: 10px auto;
  }
  p {
    line-height: 1em;
    margin: 0;
    padding: 0;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<div class="out overout">
  <p>move your mouse</p>
  <div class="in overout"><p>move your mouse</p><p>0</p></div>
  <p>0</p>
</div>
​
<div class="out enterleave">
  <p>move your mouse</p>
  <div class="in enterleave"><p>move your mouse</p><p>0</p></div>
  <p>0</p>
</div>
​
<script>
var i = 0;
$( "div.overout" )
  .mouseout(function() {
    $( "p:first", this ).text( "mouse out" );
    $( "p:last", this ).text( ++i );
  })
  .mouseover(function() {
    $( "p:first", this ).text( "mouse over" );
  });
​
var n = 0;
$( "div.enterleave" )
  .on( "mouseenter", function() {
    $( "p:first", this ).text( "mouse enter" );
  })
  .on( "mouseleave", function() {
    $( "p:first", this ).text( "mouse leave" );
    $( "p:last", this ).text( ++n );
  });
</script>
​
</body>
</html>
```
     */
    mouseout(handler?: JQuery.TypeEventHandler<TElement, null, TElement, TElement, 'mouseout'> |
                       false): this;
    /**
     * Bind an event handler to the "mouseover" JavaScript event, or trigger that event on an element.
     * @param eventData An object containing data that will be passed to the event handler.
     * @param handler A function to execute each time the event is triggered.
     * @see \`{@link https://api.jquery.com/mouseover/ }\`
     * @since 1.4.3
     * @deprecated ​ Deprecated since 3.3. Use \`{@link on }\` or \`{@link trigger }\`.
     *
     * **Cause**: The `.on()` and `.trigger()` methods can set an event handler or generate an event for any event type, and should be used instead of the shortcut methods. This message also applies to the other event shorthands, including: blur, focus, focusin, focusout, resize, scroll, dblclick, mousedown, mouseup, mousemove, mouseover, mouseout, mouseenter, mouseleave, change, select, submit, keydown, keypress, keyup, and contextmenu.
     *
     * **Solution**: Instead of `.click(fn)` use `.on("click", fn)`. Instead of `.click()` use `.trigger("click")`.
     */
    mouseover<TData>(eventData: TData,
                     handler: JQuery.TypeEventHandler<TElement, TData, TElement, TElement, 'mouseover'>): this;
    /**
     * Bind an event handler to the "mouseover" JavaScript event, or trigger that event on an element.
     * @param handler A function to execute each time the event is triggered.
     * @see \`{@link https://api.jquery.com/mouseover/ }\`
     * @since 1.0
     * @deprecated ​ Deprecated since 3.3. Use \`{@link on }\` or \`{@link trigger }\`.
     *
     * **Cause**: The `.on()` and `.trigger()` methods can set an event handler or generate an event for any event type, and should be used instead of the shortcut methods. This message also applies to the other event shorthands, including: blur, focus, focusin, focusout, resize, scroll, dblclick, mousedown, mouseup, mousemove, mouseover, mouseout, mouseenter, mouseleave, change, select, submit, keydown, keypress, keyup, and contextmenu.
     *
     * **Solution**: Instead of `.click(fn)` use `.on("click", fn)`. Instead of `.click()` use `.trigger("click")`.
     * @example ​ ````Show the number of times mouseover and mouseenter events are triggered.
mouseover fires when the pointer moves into the child element as well, while mouseenter fires only when the pointer moves into the bound element.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>mouseover demo</title>
  <style>
  div.out {
    width: 40%;
    height: 120px;
    margin: 0 15px;
    background-color: #d6edfc;
    float: left;
  }
  div.in {
    width: 60%;
    height: 60%;
    background-color: #fc0;
    margin: 10px auto;
  }
  p {
    line-height: 1em;
    margin: 0;
    padding: 0;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<div class="out overout">
  <span>move your mouse</span>
  <div class="in">
  </div>
</div>
​
<div class="out enterleave">
  <span>move your mouse</span>
  <div class="in">
  </div>
</div>
​
<script>
var i = 0;
$( "div.overout" )
  .mouseover(function() {
    i += 1;
    $( this ).find( "span" ).text( "mouse over x " + i );
  })
  .mouseout(function() {
    $( this ).find( "span" ).text( "mouse out " );
  });
​
var n = 0;
$( "div.enterleave" )
  .mouseenter(function() {
    n += 1;
    $( this ).find( "span" ).text( "mouse enter x " + n );
  })
  .mouseleave(function() {
    $( this ).find( "span" ).text( "mouse leave" );
  });
</script>
​
</body>
</html>
```
     */
    mouseover(handler?: JQuery.TypeEventHandler<TElement, null, TElement, TElement, 'mouseover'> |
                        false): this;
    /**
     * Bind an event handler to the "mouseup" JavaScript event, or trigger that event on an element.
     * @param eventData An object containing data that will be passed to the event handler.
     * @param handler A function to execute each time the event is triggered.
     * @see \`{@link https://api.jquery.com/mouseup/ }\`
     * @since 1.4.3
     * @deprecated ​ Deprecated since 3.3. Use \`{@link on }\` or \`{@link trigger }\`.
     *
     * **Cause**: The `.on()` and `.trigger()` methods can set an event handler or generate an event for any event type, and should be used instead of the shortcut methods. This message also applies to the other event shorthands, including: blur, focus, focusin, focusout, resize, scroll, dblclick, mousedown, mouseup, mousemove, mouseover, mouseout, mouseenter, mouseleave, change, select, submit, keydown, keypress, keyup, and contextmenu.
     *
     * **Solution**: Instead of `.click(fn)` use `.on("click", fn)`. Instead of `.click()` use `.trigger("click")`.
     */
    mouseup<TData>(eventData: TData,
                   handler: JQuery.TypeEventHandler<TElement, TData, TElement, TElement, 'mouseup'>): this;
    /**
     * Bind an event handler to the "mouseup" JavaScript event, or trigger that event on an element.
     * @param handler A function to execute each time the event is triggered.
     * @see \`{@link https://api.jquery.com/mouseup/ }\`
     * @since 1.0
     * @deprecated ​ Deprecated since 3.3. Use \`{@link on }\` or \`{@link trigger }\`.
     *
     * **Cause**: The `.on()` and `.trigger()` methods can set an event handler or generate an event for any event type, and should be used instead of the shortcut methods. This message also applies to the other event shorthands, including: blur, focus, focusin, focusout, resize, scroll, dblclick, mousedown, mouseup, mousemove, mouseover, mouseout, mouseenter, mouseleave, change, select, submit, keydown, keypress, keyup, and contextmenu.
     *
     * **Solution**: Instead of `.click(fn)` use `.on("click", fn)`. Instead of `.click()` use `.trigger("click")`.
     * @example ​ ````Show texts when mouseup and mousedown event triggering.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>mouseup demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p>Press mouse and release here.</p>
​
<script>
$( "p" )
  .mouseup(function() {
    $( this ).append( "<span style='color:#f00;'>Mouse up.</span>" );
  })
  .mousedown(function() {
    $( this ).append( "<span style='color:#00f;'>Mouse down.</span>" );
  });
</script>
​
</body>
</html>
```
     */
    mouseup(handler?: JQuery.TypeEventHandler<TElement, null, TElement, TElement, 'mouseup'> |
                      false): this;
    /**
     * Get the immediately following sibling of each element in the set of matched elements. If a selector is provided, it retrieves the next sibling only if it matches that selector.
     * @param selector A string containing a selector expression to match elements against.
     * @see \`{@link https://api.jquery.com/next/ }\`
     * @since 1.0
     * @example ​ ````Find the very next sibling of each disabled button and change its text &quot;this button is disabled&quot;.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>next demo</title>
  <style>
  span {
    color: blue;
    font-weight: bold;
  }
  button {
    width: 100px;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<div><button disabled="disabled">First</button> - <span></span></div>
<div><button>Second</button> - <span></span></div>
<div><button disabled="disabled">Third</button> - <span></span></div>
​
<script>
$( "button[disabled]" ).next().text( "this button is disabled" );
</script>
​
</body>
</html>
```
     * @example ​ ````Find the very next sibling of each paragraph. Keep only the ones with a class &quot;selected&quot;.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>next demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p>Hello</p>
<p class="selected">Hello Again</p>
<div><span>And Again</span></div>
​
<script>
$( "p" ).next( ".selected" ).css( "background", "yellow" );
</script>
​
</body>
</html>
```
     */
    next(selector?: JQuery.Selector): this;
    /**
     * Get all following siblings of each element in the set of matched elements, optionally filtered by a selector.
     * @param selector A string containing a selector expression to match elements against.
     * @see \`{@link https://api.jquery.com/nextAll/ }\`
     * @since 1.2
     * @example ​ ````Locate all the divs after the first and give them a class.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>nextAll demo</title>
  <style>
  div {
    width: 80px;
    height: 80px;
    background: #abc;
    border: 2px solid black;
    margin: 10px;
    float: left;
  }
  div.after {
    border-color: red;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<div>first</div>
<div>sibling<div>child</div></div>
<div>sibling</div>
<div>sibling</div>​
<script>
$( "div:first" ).nextAll().addClass( "after" );
</script>
​
</body>
</html>
```
     * @example ​ ````Locate all the paragraphs after the second child in the body and give them a class.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>nextAll demo</title>
  <style>
  div, p {
    width: 60px;
    height: 60px;
    background: #abc;
    border: 2px solid black;
    margin: 10px;
    float: left;
  }
  .after {
    border-color: red;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p>p</p>
<div>div</div>
<p>p</p>
<p>p</p>
<div>div</div>
<p>p</p>
<div>div</div>
​
<script>
$( ":nth-child(1)" ).nextAll( "p" ).addClass( "after" );
</script>
​
</body>
</html>
```
     */
    nextAll(selector?: string): this;
    /**
     * Get all following siblings of each element up to but not including the element matched by the selector, DOM node, or jQuery object passed.
     * @param selector_element _&#x40;param_ `selector_element`
     * <br>
     * * `selector` — A string containing a selector expression to indicate where to stop matching following sibling elements. <br>
     * * `element` — A DOM node or jQuery object indicating where to stop matching following sibling elements.
     * @param filter A string containing a selector expression to match elements against.
     * @see \`{@link https://api.jquery.com/nextUntil/ }\`
     * @since 1.4
     * @since 1.6
     * @example ​ ````Find the siblings that follow &lt;dt id=&quot;term-2&quot;&gt; up to the next &lt;dt&gt; and give them a red background color. Also, find &lt;dd&gt; siblings that follow &lt;dt id=&quot;term-1&quot;&gt; up to &lt;dt id=&quot;term-3&quot;&gt; and give them a green text color.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>nextUntil demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<dl>
  <dt id="term-1">term 1</dt>
  <dd>definition 1-a</dd>
  <dd>definition 1-b</dd>
  <dd>definition 1-c</dd>
  <dd>definition 1-d</dd>
  <dt id="term-2">term 2</dt>
  <dd>definition 2-a</dd>
  <dd>definition 2-b</dd>
  <dd>definition 2-c</dd>
  <dt id="term-3">term 3</dt>
  <dd>definition 3-a</dd>
  <dd>definition 3-b</dd>
</dl>
​
<script>
$( "#term-2" )
  .nextUntil( "dt" )
    .css( "background-color", "red" );
var term3 = document.getElementById( "term-3" );
$( "#term-1" )
  .nextUntil( term3, "dd" )
    .css( "color", "green" );
</script>
​
</body>
</html>
```
     */
    nextUntil(selector_element?: JQuery.Selector | Element | JQuery, filter?: JQuery.Selector): this;
    /**
     * Remove elements from the set of matched elements.
     * @param selector_function_selection _&#x40;param_ `selector_function_selection`
     * <br>
     * * `selector` — A string containing a selector expression, a DOM element, or an array of elements to match against the set. <br>
     * * `function` — A function used as a test for each element in the set. It accepts two arguments, `index`, which is
     *                the element's index in the jQuery collection, and `element`, which is the DOM element. Within the
     *                function, `this` refers to the current DOM element. <br>
     * * `selection` — An existing jQuery object to match the current set of elements against.
     * @see \`{@link https://api.jquery.com/not/ }\`
     * @since 1.0
     * @since 1.4
     * @example ​ ````Adds a border to divs that are not green or blue.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>not demo</title>
  <style>
  div {
    width: 50px;
    height: 50px;
    margin: 10px;
    float: left;
    background: yellow;
    border: 2px solid white;
  }
  .green {
    background: #8f8;
  }
  .gray {
    background: #ccc;
  }
  #blueone {
    background: #99f;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<div></div>
<div id="blueone"></div>
<div></div>
<div class="green"></div>
<div class="green"></div>
<div class="gray"></div>
<div></div>
​
<script>
$( "div" ).not( ".green, #blueone" )
  .css( "border-color", "red" );
</script>
​
</body>
</html>
```
     * @example ​ ````Removes the element with the ID &quot;selected&quot; from the set of all paragraphs.
```javascript
$( "p" ).not( $( "#selected" )[ 0 ] );
```
     * @example ​ ````Removes the element with the ID &quot;selected&quot; from the set of all paragraphs.
```javascript
$( "p" ).not( "#selected" );
```
     * @example ​ ````Removes all elements that match &quot;div p.selected&quot; from the total set of all paragraphs.
```javascript
$( "p" ).not( $( "div p.selected" ) );
```
     */
    not(selector_function_selection: JQuery.Selector | JQuery.TypeOrArray<Element> | JQuery | ((this: TElement, index: number, element: TElement) => boolean)): this;
    /**
     * Remove an event handler.
     * @param events One or more space-separated event types and optional namespaces, or just namespaces, such as
     *               "click", "keydown.myPlugin", or ".myPlugin".
     * @param selector A selector which should match the one originally passed to .on() when attaching event handlers.
     * @param handler A function to execute each time the event is triggered.
     * @see \`{@link https://api.jquery.com/off/ }\`
     * @since 1.7
     * @example ​ ````Add and remove event handlers on the colored button.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>off demo</title>
  <style>
  button {
    margin: 5px;
  }
  button#theone {
    color: red;
    background: yellow;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<button id="theone">Does nothing...</button>
<button id="bind">Add Click</button>
<button id="unbind">Remove Click</button>
<div style="display:none;">Click!</div>
​
<script>
function flash() {
  $( "div" ).show().fadeOut( "slow" );
}
$( "#bind" ).click(function() {
  $( "body" )
    .on( "click", "#theone", flash )
    .find( "#theone" )
      .text( "Can Click!" );
});
$( "#unbind" ).click(function() {
  $( "body" )
    .off( "click", "#theone", flash )
    .find( "#theone" )
      .text( "Does nothing..." );
});
</script>
​
</body>
</html>
```
     * @example ​ ````Remove just one previously bound handler by passing it as the third argument:
```javascript
var foo = function() {
  // Code to handle some kind of event
};
​
// ... Now foo will be called when paragraphs are clicked ...
$( "body" ).on( "click", "p", foo );
​
// ... Foo will no longer be called.
$( "body" ).off( "click", "p", foo );
```
     */
    off<TType extends string>(
        events: TType,
        selector: JQuery.Selector,
        handler: JQuery.TypeEventHandler<TElement, any, any, any, TType> |
                 false
    ): this;
    /**
     * Remove an event handler.
     * @param events One or more space-separated event types and optional namespaces, or just namespaces, such as
     *               "click", "keydown.myPlugin", or ".myPlugin".
     * @param selector_handler _&#x40;param_ `selector_handler`
     * <br>
     * * `selector` — A selector which should match the one originally passed to `.on()` when attaching event handlers. <br>
     * * `handler` — A handler function previously attached for the event(s), or the special value `false`.
     * @see \`{@link https://api.jquery.com/off/ }\`
     * @since 1.7
     * @example ​ ````Remove all delegated click handlers from all paragraphs:
```javascript
$( "p" ).off( "click", "**" );
```
     * @example ​ ````Unbind all delegated event handlers by their namespace:
```javascript
var validate = function() {
  // Code to validate form entries
};
​
// Delegate events under the ".validator" namespace
$( "form" ).on( "click.validator", "button", validate );
​
$( "form" ).on( "keypress.validator", "input[type='text']", validate );
​
// Remove event handlers in the ".validator" namespace
$( "form" ).off( ".validator" );
```
     */
    off<TType extends string>(
        events: TType,
        selector_handler?: JQuery.Selector |
                           JQuery.TypeEventHandler<TElement, any, any, any, TType> |
                           false
    ): this;
    /**
     * Remove an event handler.
     * @param events An object where the string keys represent one or more space-separated event types and optional
     *               namespaces, and the values represent handler functions previously attached for the event(s).
     * @param selector A selector which should match the one originally passed to .on() when attaching event handlers.
     * @see \`{@link https://api.jquery.com/off/ }\`
     * @since 1.7
     */
    off(events: JQuery.TypeEventHandlers<TElement, any, any, any>,
        selector?: JQuery.Selector): this;
    /**
     * Remove an event handler.
     * @param event A jQuery.Event object.
     * @see \`{@link https://api.jquery.com/off/ }\`
     * @since 1.7
     * @example ​ ````Remove all event handlers from all paragraphs:
```javascript
$( "p" ).off();
```
     */
    off(event?: JQuery.TriggeredEvent<TElement>): this;
    /**
     * Set the current coordinates of every element in the set of matched elements, relative to the document.
     * @param coordinates_function _&#x40;param_ `coordinates_function`
     * <br>
     * * `coordinates` — An object containing the properties `top` and `left`, which are numbers indicating the new top and
     *                   left coordinates for the elements. <br>
     * * `function` — A function to return the coordinates to set. Receives the index of the element in the collection as
     *                the first argument and the current coordinates as the second argument. The function should return an
     *                object with the new `top` and `left` properties.
     * @see \`{@link https://api.jquery.com/offset/ }\`
     * @since 1.4
     * @example ​ ````Set the offset of the second paragraph:
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>offset demo</title>
  <style>
  p {
    margin-left: 10px;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p>Hello</p><p>2nd Paragraph</p>
​
<script>
$( "p:last" ).offset({ top: 10, left: 30 });
</script>
​
</body>
</html>
```
     */
    offset(coordinates_function: JQuery.CoordinatesPartial | ((this: TElement, index: number, coords: JQuery.Coordinates) => JQuery.CoordinatesPartial)): this;
    /**
     * Get the current coordinates of the first element in the set of matched elements, relative to the document.
     * @see \`{@link https://api.jquery.com/offset/ }\`
     * @since 1.2
     * @example ​ ````Access the offset of the second paragraph:
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>offset demo</title>
  <style>
  p {
    margin-left: 10px;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p>Hello</p><p>2nd Paragraph</p>
​
<script>
var p = $( "p:last" );
var offset = p.offset();
p.html( "left: " + offset.left + ", top: " + offset.top );
</script>
​
</body>
</html>
```
     * @example ​ ````Click to see the offset.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>offset demo</title>
  <style>
  p {
    margin-left: 10px;
    color: blue;
    width: 200px;
    cursor: pointer;
  }
  span {
    color: red;
    cursor: pointer;
  }
  div.abs {
    width: 50px;
    height: 50px;
    position: absolute;
    left: 220px;
    top: 35px;
    background-color: green;
    cursor: pointer;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<div id="result">Click an element.</div>
<p>
  This is the best way to <span>find</span> an offset.
</p>
<div class="abs">
</div>
​
<script>
$( "*", document.body ).click(function( event ) {
  var offset = $( this ).offset();
  event.stopPropagation();
  $( "#result" ).text( this.tagName +
    " coords ( " + offset.left + ", " + offset.top + " )" );
});
</script>
​
</body>
</html>
```
     */
    offset(): JQuery.Coordinates | undefined;
    /**
     * Get the closest ancestor element that is positioned.
     * @see \`{@link https://api.jquery.com/offsetParent/ }\`
     * @since 1.2.6
     * @example ​ ````Find the offsetParent of item &quot;A.&quot;
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>offsetParent demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<ul class="level-1">
  <li class="item-i">I</li>
  <li class="item-ii" style="position: relative;">II
    <ul class="level-2">
      <li class="item-a">A</li>
      <li class="item-b">B
        <ul class="level-3">
          <li class="item-1">1</li>
          <li class="item-2">2</li>
          <li class="item-3">3</li>
        </ul>
      </li>
      <li class="item-c">C</li>
    </ul>
  </li>
  <li class="item-iii">III</li>
</ul>
​
<script>$( "li.item-a" ).offsetParent().css( "background-color", "red" );</script>
​
</body>
</html>
```
     */
    offsetParent(): this;
    /**
     * Attach an event handler function for one or more events to the selected elements.
     * @param events One or more space-separated event types and optional namespaces, such as "click" or "keydown.myPlugin".
     * @param selector A selector string to filter the descendants of the selected elements that trigger the event. If the
     *                 selector is null or omitted, the event is always triggered when it reaches the selected element.
     * @param data Data to be passed to the handler in event.data when an event is triggered.
     * @param handler A function to execute when the event is triggered.
     * @see \`{@link https://api.jquery.com/on/ }\`
     * @since 1.7
     */
    on<TType extends string,
       TData>(
        events: TType,
        selector: JQuery.Selector,
        data: TData,
        handler: JQuery.TypeEventHandler<TElement, TData, any, any, TType>
    ): this;
    /**
     * Attach an event handler function for one or more events to the selected elements.
     * @param events One or more space-separated event types and optional namespaces, such as "click" or "keydown.myPlugin".
     * @param selector A selector string to filter the descendants of the selected elements that trigger the event. If the
     *                 selector is null or omitted, the event is always triggered when it reaches the selected element.
     * @param data Data to be passed to the handler in event.data when an event is triggered.
     * @param handler A function to execute when the event is triggered.
     * @see \`{@link https://api.jquery.com/on/ }\`
     * @since 1.7
     */
    on<TType extends string,
       TData>(
        events: TType,
        selector: null | undefined,
        data: TData,
        handler: JQuery.TypeEventHandler<TElement, TData, TElement, TElement, TType>
    ): this;
    /**
     * Attach an event handler function for one or more events to the selected elements.
     * @param events One or more space-separated event types and optional namespaces, such as "click" or "keydown.myPlugin".
     * @param selector A selector string to filter the descendants of the selected elements that trigger the event. If the
     *                 selector is null or omitted, the event is always triggered when it reaches the selected element.
     * @param data Data to be passed to the handler in event.data when an event is triggered.
     * @param handler A function to execute when the event is triggered.
     * @see \`{@link https://api.jquery.com/on/ }\`
     * @since 1.7
     * @deprecated ​ Deprecated. Use \`{@link JQuery.Event }\` in place of \`{@link JQueryEventObject }\`.
     */
    on(events: string,
       selector: JQuery.Selector | null | undefined,
       data: any,
       handler: ((event: JQueryEventObject) => void)): this;
    /**
     * Attach an event handler function for one or more events to the selected elements.
     * @param events One or more space-separated event types and optional namespaces, such as "click" or "keydown.myPlugin".
     * @param selector A selector string to filter the descendants of the selected elements that trigger the event. If the
     *                 selector is null or omitted, the event is always triggered when it reaches the selected element.
     * @param handler A function to execute when the event is triggered. The value false is also allowed as a shorthand
     *                for a function that simply does return false.
     * @see \`{@link https://api.jquery.com/on/ }\`
     * @since 1.7
     * @example ​ ````Click any paragraph to add another after it. Note that .on() allows a click event on any paragraph--even new ones--since the event is handled by the ever-present body element after it bubbles to there.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>on demo</title>
  <style>
  p {
    background: yellow;
    font-weight: bold;
    cursor: pointer;
    padding: 5px;
  }
  p.over {
    background: #ccc;
  }
  span {
    color: red;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p>Click me!</p>
<span></span>
​
<script>
var count = 0;
$( "body" ).on( "click", "p", function() {
  $( this ).after( "<p>Another paragraph! " + (++count) + "</p>" );
});
</script>
​
</body>
</html>
```
     * @example ​ ````Display each paragraph&#39;s text in an alert box whenever it is clicked:
```javascript
$( "body" ).on( "click", "p", function() {
  alert( $( this ).text() );
});
```
     * @example ​ ````Cancel a link&#39;s default action using the .preventDefault() method:
```javascript
$( "body" ).on( "click", "a", function( event ) {
  event.preventDefault();
});
```
     */
    on<TType extends string>(
        events: TType,
        selector: JQuery.Selector,
        handler: JQuery.TypeEventHandler<TElement, undefined, any, any, TType> |
                 false
    ): this;
    /**
     * Attach an event handler function for one or more events to the selected elements.
     * @param events One or more space-separated event types and optional namespaces, such as "click" or "keydown.myPlugin".
     * @param data Data to be passed to the handler in event.data when an event is triggered.
     * @param handler A function to execute when the event is triggered.
     * @see \`{@link https://api.jquery.com/on/ }\`
     * @since 1.7
     * @example ​ ````Pass data to the event handler, which is specified here by name:
```javascript
function myHandler( event ) {
  alert( event.data.foo );
}
$( "p" ).on( "click", { foo: "bar" }, myHandler );
```
     */
    on<TType extends string,
       TData>(
        events: TType,
        data: TData,
        handler: JQuery.TypeEventHandler<TElement, TData, TElement, TElement, TType>
    ): this;
    /**
     * Attach an event handler function for one or more events to the selected elements.
     * @param events One or more space-separated event types and optional namespaces, such as "click" or "keydown.myPlugin".
     * @param selector_data _&#x40;param_ `selector_data`
     * <br>
     * * `selector` — A selector string to filter the descendants of the selected elements that trigger the event. If the
     *                selector is null or omitted, the event is always triggered when it reaches the selected element. <br>
     * * `data` — Data to be passed to the handler in event.data when an event is triggered.
     * @param handler A function to execute when the event is triggered.
     * @see \`{@link https://api.jquery.com/on/ }\`
     * @since 1.7
     * @deprecated ​ Deprecated. Use \`{@link JQuery.Event }\` in place of \`{@link JQueryEventObject }\`.
     * @example ​ ````Click any paragraph to add another after it. Note that .on() allows a click event on any paragraph--even new ones--since the event is handled by the ever-present body element after it bubbles to there.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>on demo</title>
  <style>
  p {
    background: yellow;
    font-weight: bold;
    cursor: pointer;
    padding: 5px;
  }
  p.over {
    background: #ccc;
  }
  span {
    color: red;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p>Click me!</p>
<span></span>
​
<script>
var count = 0;
$( "body" ).on( "click", "p", function() {
  $( this ).after( "<p>Another paragraph! " + (++count) + "</p>" );
});
</script>
​
</body>
</html>
```
     * @example ​ ````Display each paragraph&#39;s text in an alert box whenever it is clicked:
```javascript
$( "body" ).on( "click", "p", function() {
  alert( $( this ).text() );
});
```
     * @example ​ ````Cancel a link&#39;s default action using the .preventDefault() method:
```javascript
$( "body" ).on( "click", "a", function( event ) {
  event.preventDefault();
});
```
     * @example ​ ````Pass data to the event handler, which is specified here by name:
```javascript
function myHandler( event ) {
  alert( event.data.foo );
}
$( "p" ).on( "click", { foo: "bar" }, myHandler );
```
     */
    on(events: string,
       selector_data: any,
       handler: ((event: JQueryEventObject) => void)): this;
    /**
     * Attach an event handler function for one or more events to the selected elements.
     * @param events One or more space-separated event types and optional namespaces, such as "click" or "keydown.myPlugin".
     * @param handler A function to execute when the event is triggered. The value false is also allowed as a shorthand
     *                for a function that simply does return false.
     * @see \`{@link https://api.jquery.com/on/ }\`
     * @since 1.7
     * @example ​ ````Display a paragraph&#39;s text in an alert when it is clicked:
```javascript
$( "p" ).on( "click", function() {
  alert( $( this ).text() );
});
```
     * @example ​ ````Cancel a form submit action and prevent the event from bubbling up by returning false:
```javascript
$( "form" ).on( "submit", false );
```
     * @example ​ ````Cancel only the default action by using .preventDefault().
```javascript
$( "form" ).on( "submit", function( event ) {
  event.preventDefault();
});
```
     * @example ​ ````Stop submit events from bubbling without preventing form submit, using .stopPropagation().
```javascript
$( "form" ).on( "submit", function( event ) {
  event.stopPropagation();
});
```
     * @example ​ ````Pass data to the event handler using the second argument to .trigger()
```javascript
$( "div" ).on( "click", function( event, person ) {
  alert( "Hello, " + person.name );
});
$( "div" ).trigger( "click", { name: "Jim" } );
```
     * @example ​ ````Use the the second argument of .trigger() to pass an array of data to the event handler
```javascript
$( "div" ).on( "click", function( event, salutation, name ) {
  alert( salutation + ", " + name );
});
$( "div" ).trigger( "click", [ "Goodbye", "Jim" ] );
```
     * @example ​ ````Attach and trigger custom (non-browser) events.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>on demo</title>
  <style>
  p {
    color: red;
  }
  span {
    color: blue;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p>Has an attached custom event.</p>
<button>Trigger custom event</button>
<span style="display:none;"></span>
​
<script>
$( "p" ).on( "myCustomEvent", function( event, myName ) {
  $( this ).text( myName + ", hi there!" );
  $( "span" )
    .stop()
    .css( "opacity", 1 )
    .text( "myName = " + myName )
    .fadeIn( 30 )
    .fadeOut( 1000 );
});
$( "button" ).click(function () {
  $( "p" ).trigger( "myCustomEvent", [ "John" ] );
});
</script>
​
</body>
</html>
```
     * @example ​ ````Attach multiple events—one on mouseenter and one on mouseleave to the same element:
```javascript
$( "#cart" ).on( "mouseenter mouseleave", function( event ) {
  $( this ).toggleClass( "active" );
});
```
     */
    on<TType extends string>(
        events: TType,
        handler: JQuery.TypeEventHandler<TElement, undefined, TElement, TElement, TType> |
                 false
    ): this;
    /**
     * Attach an event handler function for one or more events to the selected elements.
     * @param events One or more space-separated event types and optional namespaces, such as "click" or "keydown.myPlugin".
     * @param handler A function to execute when the event is triggered.
     * @see \`{@link https://api.jquery.com/on/ }\`
     * @since 1.7
     * @deprecated ​ Deprecated. Use \`{@link JQuery.Event }\` in place of \`{@link JQueryEventObject }\`.
     * @example ​ ````Display a paragraph&#39;s text in an alert when it is clicked:
```javascript
$( "p" ).on( "click", function() {
  alert( $( this ).text() );
});
```
     * @example ​ ````Cancel a form submit action and prevent the event from bubbling up by returning false:
```javascript
$( "form" ).on( "submit", false );
```
     * @example ​ ````Cancel only the default action by using .preventDefault().
```javascript
$( "form" ).on( "submit", function( event ) {
  event.preventDefault();
});
```
     * @example ​ ````Stop submit events from bubbling without preventing form submit, using .stopPropagation().
```javascript
$( "form" ).on( "submit", function( event ) {
  event.stopPropagation();
});
```
     * @example ​ ````Pass data to the event handler using the second argument to .trigger()
```javascript
$( "div" ).on( "click", function( event, person ) {
  alert( "Hello, " + person.name );
});
$( "div" ).trigger( "click", { name: "Jim" } );
```
     * @example ​ ````Use the the second argument of .trigger() to pass an array of data to the event handler
```javascript
$( "div" ).on( "click", function( event, salutation, name ) {
  alert( salutation + ", " + name );
});
$( "div" ).trigger( "click", [ "Goodbye", "Jim" ] );
```
     * @example ​ ````Attach and trigger custom (non-browser) events.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>on demo</title>
  <style>
  p {
    color: red;
  }
  span {
    color: blue;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p>Has an attached custom event.</p>
<button>Trigger custom event</button>
<span style="display:none;"></span>
​
<script>
$( "p" ).on( "myCustomEvent", function( event, myName ) {
  $( this ).text( myName + ", hi there!" );
  $( "span" )
    .stop()
    .css( "opacity", 1 )
    .text( "myName = " + myName )
    .fadeIn( 30 )
    .fadeOut( 1000 );
});
$( "button" ).click(function () {
  $( "p" ).trigger( "myCustomEvent", [ "John" ] );
});
</script>
​
</body>
</html>
```
     * @example ​ ````Attach multiple events—one on mouseenter and one on mouseleave to the same element:
```javascript
$( "#cart" ).on( "mouseenter mouseleave", function( event ) {
  $( this ).toggleClass( "active" );
});
```
     */
    on(events: string,
       handler: ((event: JQueryEventObject) => void)): this;
    /**
     * Attach an event handler function for one or more events to the selected elements.
     * @param events An object in which the string keys represent one or more space-separated event types and optional
     *               namespaces, and the values represent a handler function to be called for the event(s).
     * @param selector A selector string to filter the descendants of the selected elements that will call the handler. If
     *                 the selector is null or omitted, the handler is always called when it reaches the selected element.
     * @param data Data to be passed to the handler in event.data when an event occurs.
     * @see \`{@link https://api.jquery.com/on/ }\`
     * @since 1.7
     */
    on<TData>(
        events: JQuery.TypeEventHandlers<TElement, TData, any, any>,
        selector: JQuery.Selector,
        data: TData
    ): this;
    /**
     * Attach an event handler function for one or more events to the selected elements.
     * @param events An object in which the string keys represent one or more space-separated event types and optional
     *               namespaces, and the values represent a handler function to be called for the event(s).
     * @param selector A selector string to filter the descendants of the selected elements that will call the handler. If
     *                 the selector is null or omitted, the handler is always called when it reaches the selected element.
     * @param data Data to be passed to the handler in event.data when an event occurs.
     * @see \`{@link https://api.jquery.com/on/ }\`
     * @since 1.7
     */
    on<TData>(
        events: JQuery.TypeEventHandlers<TElement, TData, TElement, TElement>,
        selector: null | undefined,
        data: TData
    ): this;
    /**
     * Attach an event handler function for one or more events to the selected elements.
     * @param events An object in which the string keys represent one or more space-separated event types and optional
     *               namespaces, and the values represent a handler function to be called for the event(s).
     * @param selector A selector string to filter the descendants of the selected elements that will call the handler. If
     *                 the selector is null or omitted, the handler is always called when it reaches the selected element.
     * @see \`{@link https://api.jquery.com/on/ }\`
     * @since 1.7
     */
    on(events: JQuery.TypeEventHandlers<TElement, undefined, any, any>,
       selector: JQuery.Selector
    ): this;
    /**
     * Attach an event handler function for one or more events to the selected elements.
     * @param events An object in which the string keys represent one or more space-separated event types and optional
     *               namespaces, and the values represent a handler function to be called for the event(s).
     * @param data Data to be passed to the handler in event.data when an event occurs.
     * @see \`{@link https://api.jquery.com/on/ }\`
     * @since 1.7
     */
    on<TData>(
        events: JQuery.TypeEventHandlers<TElement, TData, TElement, TElement>,
        data: TData
    ): this;
    /**
     * Attach an event handler function for one or more events to the selected elements.
     * @param events An object in which the string keys represent one or more space-separated event types and optional
     *               namespaces, and the values represent a handler function to be called for the event(s).
     * @see \`{@link https://api.jquery.com/on/ }\`
     * @since 1.7
     * @example ​ ````Attach multiple event handlers simultaneously using a plain object.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>on demo</title>
  <style>
  .test {
    color: #000;
    padding: .5em;
    border: 1px solid #444;
  }
  .active {
    color: #900;
  }
  .inside {
    background-color: aqua;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<div class="test">test div</div>
​
<script>
$( "div.test" ).on({
  click: function() {
    $( this ).toggleClass( "active" );
  }, mouseenter: function() {
    $( this ).addClass( "inside" );
  }, mouseleave: function() {
    $( this ).removeClass( "inside" );
  }
});
</script>
​
</body>
</html>
```
     */
    on(events: JQuery.TypeEventHandlers<TElement, undefined, TElement, TElement>): this;
    /**
     * Attach a handler to an event for the elements. The handler is executed at most once per element per event type.
     * @param events One or more space-separated event types and optional namespaces, such as "click" or "keydown.myPlugin".
     * @param selector A selector string to filter the descendants of the selected elements that trigger the event. If the
     *                 selector is null or omitted, the event is always triggered when it reaches the selected element.
     * @param data Data to be passed to the handler in event.data when an event is triggered.
     * @param handler A function to execute when the event is triggered.
     * @see \`{@link https://api.jquery.com/one/ }\`
     * @since 1.7
     */
    one<TType extends string,
        TData>(
        events: TType,
        selector: JQuery.Selector,
        data: TData,
        handler: JQuery.TypeEventHandler<TElement, TData, any, any, TType>
    ): this;
    /**
     * Attach a handler to an event for the elements. The handler is executed at most once per element per event type.
     * @param events One or more space-separated event types and optional namespaces, such as "click" or "keydown.myPlugin".
     * @param selector A selector string to filter the descendants of the selected elements that trigger the event. If the
     *                 selector is null or omitted, the event is always triggered when it reaches the selected element.
     * @param data Data to be passed to the handler in event.data when an event is triggered.
     * @param handler A function to execute when the event is triggered.
     * @see \`{@link https://api.jquery.com/one/ }\`
     * @since 1.7
     */
    one<TType extends string,
        TData>(
        events: TType,
        selector: null | undefined,
        data: TData,
        handler: JQuery.TypeEventHandler<TElement, TData, TElement, TElement, TType>
    ): this;
    /**
     * Attach a handler to an event for the elements. The handler is executed at most once per element per event type.
     * @param events One or more space-separated event types and optional namespaces, such as "click" or "keydown.myPlugin".
     * @param selector A selector string to filter the descendants of the selected elements that trigger the event. If the
     *                 selector is null or omitted, the event is always triggered when it reaches the selected element.
     * @param handler A function to execute when the event is triggered. The value false is also allowed as a shorthand
     *                for a function that simply does return false.
     * @see \`{@link https://api.jquery.com/one/ }\`
     * @since 1.7
     */
    one<TType extends string>(
        events: TType,
        selector: JQuery.Selector,
        handler: JQuery.TypeEventHandler<TElement, undefined, any, any, TType> |
                 false
    ): this;
    /**
     * Attach a handler to an event for the elements. The handler is executed at most once per element per event type.
     * @param events One or more space-separated event types and optional namespaces, such as "click" or "keydown.myPlugin".
     * @param data Data to be passed to the handler in event.data when an event is triggered.
     * @param handler A function to execute when the event is triggered.
     * @see \`{@link https://api.jquery.com/one/ }\`
     * @since 1.7
     */
    one<TType extends string,
        TData>(
        events: TType,
        data: TData,
        handler: JQuery.TypeEventHandler<TElement, TData, TElement, TElement, TType>
    ): this;
    /**
     * Attach a handler to an event for the elements. The handler is executed at most once per element per event type.
     * @param events One or more space-separated event types and optional namespaces, such as "click" or "keydown.myPlugin".
     * @param handler A function to execute when the event is triggered. The value false is also allowed as a shorthand
     *                for a function that simply does return false.
     * @see \`{@link https://api.jquery.com/one/ }\`
     * @since 1.7
     * @example ​ ````Tie a one-time click to each div.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>one demo</title>
  <style>
  div {
    width: 60px;
    height: 60px;
    margin: 5px;
    float: left;
    background: green;
    border: 10px outset;
    cursor:pointer;
  }
  p {
    color: red;
    margin: 0;
    clear: left;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<div></div>
<div></div>
<div></div>
<div></div>
<div></div>
<p>Click a green square...</p>
​
<script>
var n = 0;
$( "div" ).one( "click", function() {
  var index = $( "div" ).index( this );
  $( this ).css({
    borderStyle: "inset",
    cursor: "auto"
  });
  $( "p" ).text( "Div at index #" + index + " clicked." +
    " That's " + (++n) + " total clicks." );
});
</script>
​
</body>
</html>
```
     * @example ​ ````To display the text of all paragraphs in an alert box the first time each of them is clicked:
```javascript
$( "p" ).one( "click", function() {
  alert( $( this ).text() );
});
```
     * @example ​ ````Event handlers will trigger once per element per event type
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>one demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<div class="count">0</div>
<div class="target">Hover/click me</div>
​
<script>
var n = 0;
$(".target").one("click mouseenter", function() {
  $(".count").html(++n);
});
</script>
​
</body>
</html>
```
     */
    one<TType extends string>(
        events: TType,
        handler: JQuery.TypeEventHandler<TElement, undefined, TElement, TElement, TType>|
                 false
    ): this;
    /**
     * Attach a handler to an event for the elements. The handler is executed at most once per element per event type.
     * @param events An object in which the string keys represent one or more space-separated event types and optional
     *               namespaces, and the values represent a handler function to be called for the event(s).
     * @param selector A selector string to filter the descendants of the selected elements that will call the handler. If
     *                 the selector is null or omitted, the handler is always called when it reaches the selected element.
     * @param data Data to be passed to the handler in event.data when an event occurs.
     * @see \`{@link https://api.jquery.com/one/ }\`
     * @since 1.7
     */
    one<TData>(
        events: JQuery.TypeEventHandlers<TElement, TData, any, any>,
        selector: JQuery.Selector,
        data: TData
    ): this;
    /**
     * Attach a handler to an event for the elements. The handler is executed at most once per element per event type.
     * @param events An object in which the string keys represent one or more space-separated event types and optional
     *               namespaces, and the values represent a handler function to be called for the event(s).
     * @param selector A selector string to filter the descendants of the selected elements that will call the handler. If
     *                 the selector is null or omitted, the handler is always called when it reaches the selected element.
     * @param data Data to be passed to the handler in event.data when an event occurs.
     * @see \`{@link https://api.jquery.com/one/ }\`
     * @since 1.7
     */
    one<TData>(
        events: JQuery.TypeEventHandlers<TElement, TData, TElement, TElement>,
        selector: null | undefined,
        data: TData
    ): this;
    /**
     * Attach a handler to an event for the elements. The handler is executed at most once per element per event type.
     * @param events An object in which the string keys represent one or more space-separated event types and optional
     *               namespaces, and the values represent a handler function to be called for the event(s).
     * @param selector A selector string to filter the descendants of the selected elements that will call the handler. If
     *                 the selector is null or omitted, the handler is always called when it reaches the selected element.
     * @see \`{@link https://api.jquery.com/one/ }\`
     * @since 1.7
     */
    one(events: JQuery.TypeEventHandlers<TElement, undefined, any, any>,
        selector: JQuery.Selector): this;
    /**
     * Attach a handler to an event for the elements. The handler is executed at most once per element per event type.
     * @param events An object in which the string keys represent one or more space-separated event types and optional
     *               namespaces, and the values represent a handler function to be called for the event(s).
     * @param data Data to be passed to the handler in event.data when an event occurs.
     * @see \`{@link https://api.jquery.com/one/ }\`
     * @since 1.7
     */
    one<TData>(
        events: JQuery.TypeEventHandlers<TElement, TData, TElement, TElement>,
        data: TData
    ): this;
    /**
     * Attach a handler to an event for the elements. The handler is executed at most once per element per event type.
     * @param events An object in which the string keys represent one or more space-separated event types and optional
     *               namespaces, and the values represent a handler function to be called for the event(s).
     * @see \`{@link https://api.jquery.com/one/ }\`
     * @since 1.7
     */
    one(events: JQuery.TypeEventHandlers<TElement, undefined, TElement, TElement>): this;
    /**
     * Set the CSS outer height of each element in the set of matched elements.
     * @param value_function _&#x40;param_ `value_function`
     * <br>
     * * `value` — A number representing the number of pixels, or a number along with an optional unit of measure
     *             appended (as a string). <br>
     * * `function` — A function returning the outer height to set. Receives the index position of the element in the set
     *                and the old outer height as arguments. Within the function, `this` refers to the current element in
     *                the set.
     * @see \`{@link https://api.jquery.com/outerHeight/ }\`
     * @since 1.8.0
     * @example ​ ````Change the outer height of each div the first time it is clicked (and change its color).
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>outerHeight demo</title>
  <style>
  div {
    width: 50px;
    padding: 10px;
    height: 60px;
    float: left;
    margin: 5px;
    background: red;
    cursor: pointer;
  }
  .mod {
    background: blue;
    cursor: default;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<div>d</div>
<div>d</div>
<div>d</div>
<div>d</div>
<div>d</div>
​
<script>
var modHeight = 60;
$( "div" ).one( "click", function() {
  $( this ).outerHeight( modHeight ).addClass( "mod" );
  modHeight -= 8;
});
</script>
​
</body>
</html>
```
     */
    outerHeight(value_function: string | number | ((this: TElement, index: number, height: number) => string | number),
                includeMargin?: boolean): this;
    /**
     * Get the current computed outer height (including padding, border, and optionally margin) for the first element in the set of matched elements.
     * @param includeMargin A Boolean indicating whether to include the element's margin in the calculation.
     * @see \`{@link https://api.jquery.com/outerHeight/ }\`
     * @since 1.2.6
     * @example ​ ````Get the outerHeight of a paragraph.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>outerHeight demo</title>
  <style>
  p {
    margin: 10px;
    padding: 5px;
    border: 2px solid #666;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p>Hello</p><p></p>
​
<script>
var p = $( "p:first" );
$( "p:last" ).text(
  "outerHeight:" + p.outerHeight() +
  " , outerHeight( true ):" + p.outerHeight( true ) );
</script>
​
</body>
</html>
```
     */
    outerHeight(includeMargin?: boolean): number | undefined;
    /**
     * Set the CSS outer width of each element in the set of matched elements.
     * @param value_function _&#x40;param_ `value_function`
     * <br>
     * * `value` — A number representing the number of pixels, or a number along with an optional unit of measure
     *             appended (as a string). <br>
     * * `function` — A function returning the outer width to set. Receives the index position of the element in the set
     *                and the old outer width as arguments. Within the function, `this` refers to the current element in
     *                the set.
     * @see \`{@link https://api.jquery.com/outerWidth/ }\`
     * @since 1.8.0
     * @example ​ ````Change the outer width of each div the first time it is clicked (and change its color).
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>outerWidth demo</title>
  <style>
  div {
    width: 60px;
    padding: 10px;
    height: 50px;
    float: left;
    margin: 5px;
    background: red;
    cursor: pointer;
  }
  .mod {
    background: blue;
    cursor: default;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<div>d</div>
<div>d</div>
<div>d</div>
<div>d</div>
<div>d</div>
​
<script>
var modWidth = 60;
$( "div" ).one( "click", function() {
  $( this ).outerWidth( modWidth ).addClass( "mod" );
  modWidth -= 8;
});
</script>
​
</body>
</html>
```
     */
    outerWidth(value_function: string | number | ((this: TElement, index: number, width: number) => string | number),
               includeMargin?: boolean): this;
    /**
     * Get the current computed outer width (including padding, border, and optionally margin) for the first element in the set of matched elements.
     * @param includeMargin A Boolean indicating whether to include the element's margin in the calculation.
     * @see \`{@link https://api.jquery.com/outerWidth/ }\`
     * @since 1.2.6
     * @example ​ ````Get the outerWidth of a paragraph.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>outerWidth demo</title>
  <style>
  p {
    margin: 10px;
    padding: 5px;
    border: 2px solid #666;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p>Hello</p><p></p>
​
<script>
var p = $( "p:first" );
$( "p:last" ).text(
  "outerWidth:" + p.outerWidth() +
  " , outerWidth( true ):" + p.outerWidth( true ) );
</script>
​
</body>
</html>
```
     */
    outerWidth(includeMargin?: boolean): number | undefined;
    /**
     * Get the parent of each element in the current set of matched elements, optionally filtered by a selector.
     * @param selector A string containing a selector expression to match elements against.
     * @see \`{@link https://api.jquery.com/parent/ }\`
     * @since 1.0
     * @example ​ ````Shows the parent of each element as (parent &gt; child).  Check the View Source to see the raw html.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>parent demo</title>
  <style>
  div, p {
    margin: 10px;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<div>div,
  <span>span, </span>
  <b>b </b>
</div>
​
<p>p,
  <span>span,
    <em>em </em>
  </span>
</p>
​
<div>div,
  <strong>strong,
    <span>span, </span>
    <em>em,
      <b>b, </b>
    </em>
  </strong>
  <b>b </b>
</div>
​
<script>
$( "*", document.body ).each(function() {
  var parentTag = $( this ).parent().get( 0 ).tagName;
  $( this ).prepend( document.createTextNode( parentTag + " > " ) );
});
</script>
​
</body>
</html>
```
     * @example ​ ````Find the parent element of each paragraph with a class &quot;selected&quot;.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>parent demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<div><p>Hello</p></div>
<div class="selected"><p>Hello Again</p></div>
​
<script>
$( "p" ).parent( ".selected" ).css( "background", "yellow" );
</script>
​
</body>
</html>
```
     */
    parent(selector?: JQuery.Selector): this;
    /**
     * Get the ancestors of each element in the current set of matched elements, optionally filtered by a selector.
     * @param selector A string containing a selector expression to match elements against.
     * @see \`{@link https://api.jquery.com/parents/ }\`
     * @since 1.0
     * @example ​ ````Find all parent elements of each b.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>parents demo</title>
  <style>
  b, span, p, html body {
    padding: .5em;
    border: 1px solid;
  }
  b {
    color: blue;
  }
  strong {
    color: red;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<div>
  <p>
    <span>
      <b>My parents are: </b>
    </span>
  </p>
</div>
​
<script>
var parentEls = $( "b" ).parents()
  .map(function() {
    return this.tagName;
  })
  .get()
  .join( ", " );
$( "b" ).append( "<strong>" + parentEls + "</strong>" );
</script>
​
</body>
</html>
```
     * @example ​ ````Click to find all unique div parent elements of each span.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>parents demo</title>
  <style>
  p, div, span {
    margin: 2px;
    padding: 1px;
  }
  div {
    border: 2px white solid;
  }
  span {
    cursor: pointer;
    font-size: 12px;
  }
  .selected {
    color: blue;
  }
  b {
    color: red;
    display: block;
    font-size: 14px;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p>
  <div>
    <div><span>Hello</span></div>
      <span>Hello Again</span>
    </div>
    <div>
      <span>And Hello Again</span>
    </div>
  </p>
  <b>Click Hellos to toggle their parents.</b>
​
<script>
function showParents() {
  $( "div" ).css( "border-color", "white" );
  var len = $( "span.selected" )
    .parents( "div" )
      .css( "border", "2px red solid" )
      .length;
  $( "b" ).text( "Unique div parents: " + len );
}
$( "span" ).click(function() {
  $( this ).toggleClass( "selected" );
  showParents();
});
</script>
​
</body>
</html>
```
     */
    parents(selector?: JQuery.Selector): this;
    /**
     * Get the ancestors of each element in the current set of matched elements, up to but not including the element matched by the selector, DOM node, or jQuery object.
     * @param selector_element _&#x40;param_ `selector_element`
     * <br>
     * * `selector` — A string containing a selector expression to indicate where to stop matching ancestor elements. <br>
     * * `element` — A DOM node or jQuery object indicating where to stop matching ancestor elements.
     * @param filter A string containing a selector expression to match elements against.
     * @see \`{@link https://api.jquery.com/parentsUntil/ }\`
     * @since 1.4
     * @since 1.6
     * @example ​ ````Find the ancestors of &lt;li class=&quot;item-a&quot;&gt; up to &lt;ul class=&quot;level-1&quot;&gt; and give them a red background color. Also, find ancestors of &lt;li class=&quot;item-2&quot;&gt; that have a class of &quot;yes&quot; up to &lt;ul class=&quot;level-1&quot;&gt; and give them a green border.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>parentsUntil demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<ul class="level-1 yes">
  <li class="item-i">I</li>
  <li class="item-ii">II
    <ul class="level-2 yes">
      <li class="item-a">A</li>
      <li class="item-b">B
        <ul class="level-3">
          <li class="item-1">1</li>
          <li class="item-2">2</li>
          <li class="item-3">3</li>
        </ul>
      </li>
      <li class="item-c">C</li>
    </ul>
  </li>
  <li class="item-iii">III</li>
</ul>
​
<script>
$( "li.item-a" )
  .parentsUntil( ".level-1" )
    .css( "background-color", "red" );
​
$( "li.item-2" )
  .parentsUntil( $( "ul.level-1" ), ".yes" )
    .css( "border", "3px solid green" );
</script>
​
</body>
</html>
```
     */
    parentsUntil(selector_element?: JQuery.Selector | Element | JQuery, filter?: JQuery.Selector): this;
    /**
     * Get the current coordinates of the first element in the set of matched elements, relative to the offset parent.
     * @see \`{@link https://api.jquery.com/position/ }\`
     * @since 1.2
     * @example ​ ````Access the position of the second paragraph:
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>position demo</title>
  <style>
  div {
    padding: 15px;
  }
  p {
    margin-left: 10px;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<div>
  <p>Hello</p>
</div>
<p></p>
​
<script>
var p = $( "p:first" );
var position = p.position();
$( "p:last" ).text( "left: " + position.left + ", top: " + position.top );
</script>
​
</body>
</html>
```
     */
    position(): JQuery.Coordinates;
    /**
     * Insert content, specified by the parameter, to the beginning of each element in the set of matched elements.
     * @param contents One or more additional DOM elements, text nodes, arrays of elements and text nodes, HTML strings, or
     *                 jQuery objects to insert at the beginning of each element in the set of matched elements.
     * @see \`{@link https://api.jquery.com/prepend/ }\`
     * @since 1.0
     * @example ​ ````Prepends some HTML to all paragraphs.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>prepend demo</title>
  <style>
  p {
    background: yellow;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p>there, friend!</p>
<p>amigo!</p>
​
<script>
$( "p" ).prepend( "<b>Hello </b>" );
</script>
​
</body>
</html>
```
     * @example ​ ````Prepends a DOM Element to all paragraphs.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>prepend demo</title>
  <style>
  p {
    background: yellow;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p>is what I'd say</p>
<p>is what I said</p>
​
<script>
$( "p" ).prepend( document.createTextNode( "Hello " ) );
</script>
​
</body>
</html>
```
     * @example ​ ````Prepends a jQuery object (similar to an Array of DOM Elements) to all paragraphs.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>prepend demo</title>
  <style>
  p {
    background: yellow;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p> is what was said.</p><b>Hello</b>
​
<script>
$( "p" ).prepend( $( "b" ) );
</script>
​
</body>
</html>
```
     */
    prepend(...contents: Array<JQuery.htmlString | JQuery.TypeOrArray<JQuery.Node | JQuery<JQuery.Node>>>): this;
    /**
     * Insert content, specified by the parameter, to the beginning of each element in the set of matched elements.
     * @param funсtion A function that returns an HTML string, DOM element(s), text node(s), or jQuery object to insert at
     *                 the beginning of each element in the set of matched elements. Receives the index position of the
     *                 element in the set and the old HTML value of the element as arguments. Within the function, `this`
     *                 refers to the current element in the set.
     * @see \`{@link https://api.jquery.com/prepend/ }\`
     * @since 1.4
     */
    prepend(funсtion: (this: TElement, index: number, html: string) => JQuery.htmlString | JQuery.TypeOrArray<JQuery.Node | JQuery<JQuery.Node>>): this;
    /**
     * Insert every element in the set of matched elements to the beginning of the target.
     * @param target A selector, element, HTML string, array of elements, or jQuery object; the matched set of elements
     *               will be inserted at the beginning of the element(s) specified by this parameter.
     * @see \`{@link https://api.jquery.com/prependTo/ }\`
     * @since 1.0
     * @example ​ ````Prepend all spans to the element with the ID &quot;foo&quot; (Check .prepend() documentation for more examples)
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>prependTo demo</title>
  <style>
  div {
    background: yellow;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<div id="foo">FOO!</div>
<span>I have something to say... </span>
​
<script>
$( "span" ).prependTo( "#foo" );
</script>
​
</body>
</html>
```
     */
    prependTo(target: JQuery.Selector | JQuery.htmlString | JQuery.TypeOrArray<Element | DocumentFragment> | JQuery): this;
    /**
     * Get the immediately preceding sibling of each element in the set of matched elements. If a selector is provided, it retrieves the previous sibling only if it matches that selector.
     * @param selector A string containing a selector expression to match elements against.
     * @see \`{@link https://api.jquery.com/prev/ }\`
     * @since 1.0
     * @example ​ ````Find the very previous sibling of each div.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>prev demo</title>
  <style>
  div {
    width: 40px;
    height: 40px;
    margin: 10px;
    float: left;
    border: 2px blue solid;
    padding: 2px;
  }
  span {
    font-size: 14px;
  }
  p {
    clear: left;
    margin: 10px;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<div></div>
<div></div>
<div><span>has child</span></div>
<div></div>
<div></div>
<div></div>
<div id="start"></div>
<div></div>
<p><button>Go to Prev</button></p>
​
<script>
var $curr = $( "#start" );
$curr.css( "background", "#f99" );
$( "button" ).click(function() {
  $curr = $curr.prev();
  $( "div" ).css( "background", "" );
  $curr.css( "background", "#f99" );
});
</script>
​
</body>
</html>
```
     * @example ​ ````For each paragraph, find the very previous sibling that has a class &quot;selected&quot;.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>prev demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<div><span>Hello</span></div>
<p class="selected">Hello Again</p>
<p>And Again</p>
​
<script>
$( "p" ).prev( ".selected" ).css( "background", "yellow" );
</script>
​
</body>
</html>
```
     */
    prev(selector?: JQuery.Selector): this;
    /**
     * Get all preceding siblings of each element in the set of matched elements, optionally filtered by a selector.
     * @param selector A string containing a selector expression to match elements against.
     * @see \`{@link https://api.jquery.com/prevAll/ }\`
     * @since 1.2
     * @example ​ ````Locate all the divs preceding the last div and give them a class.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>prevAll demo</title>
  <style>
  div {
    width: 70px;
    height: 70px;
    background: #abc;
    border: 2px solid black;
    margin: 10px;
    float: left;
  }
  div.before {
    border-color: red;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<div></div>
<div></div>
<div></div>
<div></div>
​
<script>
$( "div:last" ).prevAll().addClass( "before" );
</script>
​
</body>
</html>
```
     */
    prevAll(selector?: JQuery.Selector): this;
    /**
     * Get all preceding siblings of each element up to but not including the element matched by the selector, DOM node, or jQuery object.
     * @param selector_element _&#x40;param_ `selector_element`
     * <br>
     * * `selector` — A string containing a selector expression to indicate where to stop matching preceding sibling elements. <br>
     * * `element` — A DOM node or jQuery object indicating where to stop matching preceding sibling elements.
     * @param filter A string containing a selector expression to match elements against.
     * @see \`{@link https://api.jquery.com/prevUntil/ }\`
     * @since 1.4
     * @since 1.6
     * @example ​ ````Find the siblings that precede &lt;dt id=&quot;term-2&quot;&gt; up to the preceding &lt;dt&gt; and give them a red background color. Also, find previous &lt;dd&gt; siblings of &lt;dt id=&quot;term-3&quot;&gt; up to &lt;dt id=&quot;term-1&quot;&gt; and give them a green text color.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>prevUntil demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<dl>
  <dt id="term-1">term 1</dt>
  <dd>definition 1-a</dd>
  <dd>definition 1-b</dd>
  <dd>definition 1-c</dd>
  <dd>definition 1-d</dd>
​
  <dt id="term-2">term 2</dt>
  <dd>definition 2-a</dd>
  <dd>definition 2-b</dd>
  <dd>definition 2-c</dd>
​
  <dt id="term-3">term 3</dt>
  <dd>definition 3-a</dd>
  <dd>definition 3-b</dd>
</dl>
​
<script>
$( "#term-2" ).prevUntil( "dt" )
  .css( "background-color", "red" );
​
var term1 = document.getElementById( "term-1" );
$( "#term-3" ).prevUntil( term1, "dd" )
  .css( "color", "green" );
</script>
​
</body>
</html>
```
     */
    prevUntil(selector_element?: JQuery.Selector | Element | JQuery, filter?: JQuery.Selector): this;
    /**
     * Return a Promise object to observe when all actions of a certain type bound to the collection, queued or not, have finished.
     * @param type The type of queue that needs to be observed.
     * @param target Object onto which the promise methods have to be attached
     * @see \`{@link https://api.jquery.com/promise/ }\`
     * @since 1.6
     */
    promise<T extends object>(type: string, target: T): T & JQuery.Promise<this>;
    /**
     * Return a Promise object to observe when all actions of a certain type bound to the collection, queued or not, have finished.
     * @param target Object onto which the promise methods have to be attached
     * @see \`{@link https://api.jquery.com/promise/ }\`
     * @since 1.6
     */
    promise<T extends object>(target: T): T & JQuery.Promise<this>;
    /**
     * Return a Promise object to observe when all actions of a certain type bound to the collection, queued or not, have finished.
     * @param type The type of queue that needs to be observed.
     * @see \`{@link https://api.jquery.com/promise/ }\`
     * @since 1.6
     * @example ​ ````Using .promise() on a collection with no active animation returns a resolved Promise:
```javascript
var div = $( "<div>" );
​
div.promise().done(function( arg1 ) {
  // Will fire right away and alert "true"
  alert( this === div && arg1 === div );
});
```
     * @example ​ ````Resolve the returned Promise when all animations have ended (including those initiated in the animation callback or added later on):
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>promise demo</title>
  <style>
  div {
    height: 50px;
    width: 50px;
    float: left;
    margin-right: 10px;
    display: none;
    background-color: #090;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<button>Go</button>
<p>Ready...</p>
<div></div>
<div></div>
<div></div>
<div></div>
​
<script>
$( "button" ).on( "click", function() {
  $( "p" ).append( "Started..." );
​
  $( "div" ).each(function( i ) {
    $( this ).fadeIn().fadeOut( 1000 * ( i + 1 ) );
  });
​
  $( "div" ).promise().done(function() {
    $( "p" ).append( " Finished! " );
  });
});
</script>
​
</body>
</html>
```
     * @example ​ ````Resolve the returned Promise using a $.when() statement (the .promise() method makes it possible to do this with jQuery collections):
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>promise demo</title>
  <style>
  div {
    height: 50px;
    width: 50px;
    float: left;
    margin-right: 10px;
    display: none;
    background-color: #090;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<button>Go</button>
<p>Ready...</p>
<div></div>
<div></div>
<div></div>
<div></div>
​
<script>
var effect = function() {
  return $( "div" ).fadeIn( 800 ).delay( 1200 ).fadeOut();
};
​
$( "button" ).on( "click", function() {
  $( "p" ).append( " Started... " );
​
  $.when( effect() ).done(function() {
    $( "p" ).append( " Finished! " );
  });
});
</script>
​
</body>
</html>
```
     */
    promise(type?: string): JQuery.Promise<this>;
    /**
     * Set one or more properties for the set of matched elements.
     * @param propertyName The name of the property to set.
     * @param value_function _&#x40;param_ `value_function`
     * <br>
     * * `value` — A value to set for the property. <br>
     * * `function` — A function returning the value to set. Receives the index position of the element in the set and the
     *                old property value as arguments. Within the function, the keyword `this` refers to the current element.
     * @see \`{@link https://api.jquery.com/prop/ }\`
     * @since 1.6
     */
    prop(propertyName: string,
         value_function: string | number | boolean | symbol | object | null | undefined | ((this: TElement, index: number, oldPropertyValue: any) => any)): this;
    /**
     * Set one or more properties for the set of matched elements.
     * @param properties An object of property-value pairs to set.
     * @see \`{@link https://api.jquery.com/prop/ }\`
     * @since 1.6
     * @example ​ ````Disable all checkboxes on the page.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>prop demo</title>
  <style>
  img {
    padding: 10px;
  }
  div {
    color: red;
    font-size: 24px;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
  <input type="checkbox" checked="checked">
  <input type="checkbox">
  <input type="checkbox">
  <input type="checkbox" checked="checked">
​
<script>
$( "input[type='checkbox']" ).prop({
  disabled: true
});
</script>
​
</body>
</html>
```
     */
    prop(properties: JQuery.PlainObject): this;
    /**
     * Get the value of a property for the first element in the set of matched elements.
     * @param propertyName The name of the property to get.
     * @see \`{@link https://api.jquery.com/prop/ }\`
     * @since 1.6
     * @example ​ ````Display the checked property and attribute of a checkbox as it changes.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>prop demo</title>
  <style>
  p {
    margin: 20px 0 0;
  }
  b {
    color: blue;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<input id="check1" type="checkbox" checked="checked">
<label for="check1">Check me</label>
<p></p>
​
<script>
$( "input" ).change(function() {
  var $input = $( this );
  $( "p" ).html(
    ".attr( \"checked\" ): <b>" + $input.attr( "checked" ) + "</b><br>" +
    ".prop( \"checked\" ): <b>" + $input.prop( "checked" ) + "</b><br>" +
    ".is( \":checked\" ): <b>" + $input.is( ":checked" ) + "</b>" );
}).change();
</script>
​
</body>
</html>
```
     */
    prop(propertyName: string): any;
    /**
     * Add a collection of DOM elements onto the jQuery stack.
     * @param elements An array of elements to push onto the stack and make into a new jQuery object.
     * @param name The name of a jQuery method that generated the array of elements.
     * @param args The arguments that were passed in to the jQuery method (for serialization).
     * @see \`{@link https://api.jquery.com/pushStack/ }\`
     * @since 1.3
     */
    pushStack(elements: ArrayLike<Element>, name: string, args: any[]): this;
    /**
     * Add a collection of DOM elements onto the jQuery stack.
     * @param elements An array of elements to push onto the stack and make into a new jQuery object.
     * @see \`{@link https://api.jquery.com/pushStack/ }\`
     * @since 1.0
     * @example ​ ````Add some elements onto the jQuery stack, then pop back off again.
```javascript
jQuery([])
  .pushStack( document.getElementsByTagName( "div" ) )
  .remove()
  .end();
```
     */
    pushStack(elements: ArrayLike<Element>): this;
    /**
     * Manipulate the queue of functions to be executed, once for each matched element.
     * @param queueName A string containing the name of the queue. Defaults to fx, the standard effects queue.
     * @param newQueue The new function to add to the queue, with a function to call that will dequeue the next item.
     *                 An array of functions to replace the current queue contents.
     * @see \`{@link https://api.jquery.com/queue/ }\`
     * @since 1.2
     * @example ​ ````Set a queue array to delete the queue.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>queue demo</title>
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
  $( "div" )
    .show( "slow" )
    .animate({ left: "+=200" }, 5000 )
    .queue(function() {
      $( this ).addClass( "newcolor" ).dequeue();
    })
    .animate({ left: '-=200' }, 1500 )
    .queue(function() {
      $( this ).removeClass( "newcolor" ).dequeue();
    })
    .slideUp();
});
$( "#stop" ).click(function() {
  $( "div" )
    .queue( "fx", [] )
    .stop();
});
</script>
​
</body>
</html>
```
     */
    queue(queueName: string, newQueue: JQuery.TypeOrArray<JQuery.QueueFunction<TElement>>): this;
    /**
     * Manipulate the queue of functions to be executed, once for each matched element.
     * @param newQueue The new function to add to the queue, with a function to call that will dequeue the next item.
     *                 An array of functions to replace the current queue contents.
     * @see \`{@link https://api.jquery.com/queue/ }\`
     * @since 1.2
     * @example ​ ````Queue a custom function.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>queue demo</title>
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
  $( "div" )
    .show( "slow" )
    .animate({ left: "+=200" }, 2000 )
    .queue(function() {
      $( this ).addClass( "newcolor" ).dequeue();
    })
    .animate({ left: "-=200" }, 500 )
    .queue(function() {
      $( this ).removeClass( "newcolor" ).dequeue();
    })
    .slideUp();
});
</script>
​
</body>
</html>
```
     */
    queue(newQueue: JQuery.TypeOrArray<JQuery.QueueFunction<TElement>>): this;
    /**
     * Show the queue of functions to be executed on the matched elements.
     * @param queueName A string containing the name of the queue. Defaults to fx, the standard effects queue.
     * @see \`{@link https://api.jquery.com/queue/ }\`
     * @since 1.2
     * @example ​ ````Show the length of the queue.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>queue demo</title>
  <style>
  div {
    margin: 3px;
    width: 40px;
    height: 40px;
    position: absolute;
    left: 0px;
    top: 60px;
    background: green;
    display: none;
  }
  div.newcolor {
    background: blue;
  }
  p {
    color: red;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p>The queue length is: <span></span></p>
<div></div>
​
<script>
var div = $( "div" );
​
function runIt() {
  div
    .show( "slow" )
    .animate({ left: "+=200" }, 2000 )
    .slideToggle( 1000 )
    .slideToggle( "fast" )
    .animate({ left: "-=200" }, 1500 )
    .hide( "slow" )
    .show( 1200 )
    .slideUp( "normal", runIt );
}
​
function showIt() {
  var n = div.queue( "fx" );
  $( "span" ).text( n.length );
  setTimeout( showIt, 100 );
}
​
runIt();
showIt();
</script>
​
</body>
</html>
```
     */
    queue(queueName?: string): JQuery.Queue<Node>;
    /**
     * Specify a function to execute when the DOM is fully loaded.
     * @param handler A function to execute after the DOM is ready.
     * @see \`{@link https://api.jquery.com/ready/ }\`
     * @since 1.0
     * @deprecated ​ Deprecated since 3.0. Use `jQuery(function() { })`.
     * @example ​ ````Display a message when the DOM is loaded.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>ready demo</title>
  <style>
  p {
    color: red;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
  <script>
​
  $(function() {
    $( "p" ).text( "The DOM is now loaded and can be manipulated." );
  });
​
  </script>
</head>
<body>
​
<p>Not loaded yet.</p>
​
</body>
</html>
```
     */
    ready(handler: ($: JQueryStatic) => void): this;
    /**
     * Remove the set of matched elements from the DOM.
     * @param selector A selector expression that filters the set of matched elements to be removed.
     * @see \`{@link https://api.jquery.com/remove/ }\`
     * @since 1.0
     * @example ​ ````Removes all paragraphs from the DOM
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>remove demo</title>
  <style>
  p {
    background: yellow;
    margin: 6px 0;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p>Hello</p>
how are
<p>you?</p>
<button>Call remove() on paragraphs</button>
​
<script>
$( "button" ).click(function() {
  $( "p" ).remove();
});
</script>
​
</body>
</html>
```
     * @example ​ ````Removes all paragraphs that contain &quot;Hello&quot; from the DOM.  Analogous to doing $(&quot;p&quot;).filter(&quot;:contains(&#39;Hello&#39;)&quot;).remove().
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>remove demo</title>
  <style>
  p {
    background: yellow;
    margin: 6px 0;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p class="hello">Hello</p>
how are
<p>you?</p>
<button>Call remove( ":contains('Hello')" ) on paragraphs</button>
​
<script>
$( "button" ).click(function() {
  $( "p" ).remove( ":contains('Hello')" );
});
</script>
​
</body>
</html>
```
     */
    remove(selector?: string): this;
    /**
     * Remove an attribute from each element in the set of matched elements.
     * @param attributeName An attribute to remove; as of version 1.7, it can be a space-separated list of attributes.
     * @see \`{@link https://api.jquery.com/removeAttr/ }\`
     * @since 1.0
     * @example ​ ````Clicking the button changes the title of the input next to it. Move the mouse pointer over the text input to see the effect of adding and removing the title attribute.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>removeAttr demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<button>Change title</button>
<input type="text" title="hello there">
<div id="log"></div>
​
<script>
(function() {
  var inputTitle = $( "input" ).attr( "title" );
  $( "button" ).click(function() {
    var input = $( this ).next();
​
    if ( input.attr( "title" ) === inputTitle ) {
      input.removeAttr( "title" )
    } else {
      input.attr( "title", inputTitle );
    }
​
    $( "#log" ).html( "input title is now " + input.attr( "title" ) );
  });
})();
</script>
​
</body>
</html>
```
     */
    removeAttr(attributeName: string): this;
    /**
     * Remove a single class, multiple classes, or all classes from each element in the set of matched elements.
     * @param className_function _&#x40;param_ `className_function`
     * <br>
     * * `className` — One or more space-separated classes to be removed from the class attribute of each matched element. <br>
     * * `function` — A function returning one or more space-separated class names to be removed. Receives the index
     *                position of the element in the set and the old class value as arguments.
     * @see \`{@link https://api.jquery.com/removeClass/ }\`
     * @since 1.0
     * @since 1.4
     * @since 3.3
     * @example ​ ````Remove the class &#39;blue&#39; from the matched elements.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>removeClass demo</title>
  <style>
  p {
    margin: 4px;
    font-size: 16px;
    font-weight: bolder;
  }
  .blue {
    color: blue;
  }
  .under {
    text-decoration: underline;
  }
  .highlight {
    background: yellow;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p class="blue under">Hello</p>
<p class="blue under highlight">and</p>
<p class="blue under">then</p>
<p class="blue under">Goodbye</p>
​
<script>
$( "p:even" ).removeClass( "blue" );
</script>
​
</body>
</html>
```
     * @example ​ ````Remove the class &#39;blue&#39; and &#39;under&#39; from the matched elements.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>removeClass demo</title>
  <style>
  p {
    margin: 4px;
    font-size: 16px;
    font-weight: bolder;
  }
  .blue {
    color: blue;
  }
  .under {
    text-decoration: underline;
  }
  .highlight {
    background: yellow;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p class="blue under">Hello</p>
<p class="blue under highlight">and</p>
<p class="blue under">then</p>
<p class="blue under">Goodbye</p>
​
<script>
$( "p:odd" ).removeClass( "blue under" );
</script>
​
</body>
</html>
```
     * @example ​ ````Remove all the classes from the matched elements.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>removeClass demo</title>
  <style>
  p {
    margin: 4px;
    font-size: 16px;
    font-weight: bolder;
  }
  .blue {
    color: blue;
  }
  .under {
    text-decoration: underline;
  }
  .highlight {
    background: yellow;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p class="blue under">Hello</p>
<p class="blue under highlight">and</p>
<p class="blue under">then</p>
<p class="blue under">Goodbye</p>
​
<script>
$( "p:eq(1)" ).removeClass();
</script>
​
</body>
</html>
```
     */
    removeClass(className_function?: JQuery.TypeOrArray<string> | ((this: TElement, index: number, className: string) => string)): this;
    /**
     * Remove a previously-stored piece of data.
     * @param name A string naming the piece of data to delete.
     *             An array or space-separated string naming the pieces of data to delete.
     * @see \`{@link https://api.jquery.com/removeData/ }\`
     * @since 1.2.3
     * @since 1.7
     * @example ​ ````Set a data store for 2 names then remove one of them.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>removeData demo</title>
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
$( "span:eq(0)" ).text( "" + $( "div" ).data( "test1" ) );
$( "div" ).data( "test1", "VALUE-1" );
$( "div" ).data( "test2", "VALUE-2" );
$( "span:eq(1)" ).text( "" + $( "div").data( "test1" ) );
$( "div" ).removeData( "test1" );
$( "span:eq(2)" ).text( "" + $( "div" ).data( "test1" ) );
$( "span:eq(3)" ).text( "" + $( "div" ).data( "test2" ) );
</script>
​
</body>
</html>
```
     */
    removeData(name?: JQuery.TypeOrArray<string>): this;
    /**
     * Remove a property for the set of matched elements.
     * @param propertyName The name of the property to remove.
     * @see \`{@link https://api.jquery.com/removeProp/ }\`
     * @since 1.6
     * @example ​ ````Set a numeric property on a paragraph and then remove it.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>removeProp demo</title>
  <style>
  img {
    padding: 10px;
  }
  div {
    color: red;
    font-size: 24px;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
  <p></p>
​
<script>
para = $( "p" );
para
  .prop( "luggageCode", 1234 )
  .append( "The secret luggage code is: ", String( para.prop( "luggageCode" ) ), ". " )
  .removeProp( "luggageCode" )
  .append( "Now the secret luggage code is: ", String( para.prop( "luggageCode" ) ), ". " );
</script>
​
</body>
</html>
```
     */
    removeProp(propertyName: string): this;
    /**
     * Replace each target element with the set of matched elements.
     * @param target A selector string, jQuery object, DOM element, or array of elements indicating which element(s) to replace.
     * @see \`{@link https://api.jquery.com/replaceAll/ }\`
     * @since 1.2
     * @example ​ ````Replace all the paragraphs with bold words.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>replaceAll demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p>Hello</p>
<p>cruel</p>
<p>World</p>
​
<script>
$( "<b>Paragraph. </b>" ).replaceAll( "p" );
</script>
​
</body>
</html>
```
     */
    replaceAll(target: JQuery.Selector | JQuery | JQuery.TypeOrArray<Element>): this;
    /**
     * Replace each element in the set of matched elements with the provided new content and return the set of elements that was removed.
     * @param newContent_function _&#x40;param_ `newContent_function`
     * <br>
     * * `newContent` — The content to insert. May be an HTML string, DOM element, array of DOM elements, or jQuery object. <br>
     * * `function` — A function that returns content with which to replace the set of matched elements.
     * @see \`{@link https://api.jquery.com/replaceWith/ }\`
     * @since 1.2
     * @since 1.4
     * @example ​ ````On click, replace the button with a div containing the same word.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>replaceWith demo</title>
  <style>
  button {
    display: block;
    margin: 3px;
    color: red;
    width: 200px;
  }
  div {
    color: red;
    border: 2px solid blue;
    width: 200px;
    margin: 3px;
    text-align: center;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<button>First</button>
<button>Second</button>
<button>Third</button>
​
<script>
$( "button" ).click(function() {
  $( this ).replaceWith( "<div>" + $( this ).text() + "</div>" );
});
</script>
​
</body>
</html>
```
     * @example ​ ````Replace all paragraphs with bold words.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>replaceWith demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p>Hello</p>
<p>cruel</p>
<p>World</p>
​
<script>
$( "p" ).replaceWith( "<b>Paragraph. </b>" );
</script>
​
</body>
</html>
```
     * @example ​ ````On click, replace each paragraph with a div that is already in the DOM and selected with the $() function. Notice it doesn&#39;t clone the object but rather moves it to replace the paragraph.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>replaceWith demo</title>
  <style>
  div {
    border: 2px solid blue;
    color: red;
    margin: 3px;
  }
  p {
    border: 2px solid red;
    color: blue;
    margin: 3px;
    cursor: pointer;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
  <p>Hello</p>
  <p>cruel</p>
  <p>World</p>
  <div>Replaced!</div>
​
<script>
$( "p" ).click(function() {
  $( this ).replaceWith( $( "div" ) );
});
</script>
​
</body>
</html>
```
     * @example ​ ````On button click, replace the containing div with its child divs and append the class name of the selected element to the paragraph.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>replaceWith demo</title>
  <style>
  .container {
    background-color: #991;
  }
  .inner {
    color: #911;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p>
  <button>Replace!</button>
</p>
<div class="container">
  <div class="inner">Scooby</div>
  <div class="inner">Dooby</div>
  <div class="inner">Doo</div>
</div>
​
<script>
$( "button" ).on( "click", function() {
  var $container = $( "div.container" ).replaceWith(function() {
    return $( this ).contents();
  });
​
  $( "p" ).append( $container.attr( "class" ) );
});
</script>
​
</body>
</html>
```
     */
    replaceWith(newContent_function: JQuery.htmlString |
                                     JQuery<JQuery.Node> |
                                     JQuery.TypeOrArray<Element> |
                                     JQuery.Node |
                                     ((this: TElement, index: number, oldhtml: JQuery.htmlString) => JQuery.htmlString |
                                                                                                     JQuery<JQuery.Node> |
                                                                                                     JQuery.TypeOrArray<Element> |
                                                                                                     JQuery.Node)): this;
    /**
     * Bind an event handler to the "resize" JavaScript event, or trigger that event on an element.
     * @param eventData An object containing data that will be passed to the event handler.
     * @param handler A function to execute each time the event is triggered.
     * @see \`{@link https://api.jquery.com/resize/ }\`
     * @since 1.4.3
     * @deprecated ​ Deprecated since 3.3. Use \`{@link on }\` or \`{@link trigger }\`.
     *
     * **Cause**: The `.on()` and `.trigger()` methods can set an event handler or generate an event for any event type, and should be used instead of the shortcut methods. This message also applies to the other event shorthands, including: blur, focus, focusin, focusout, resize, scroll, dblclick, mousedown, mouseup, mousemove, mouseover, mouseout, mouseenter, mouseleave, change, select, submit, keydown, keypress, keyup, and contextmenu.
     *
     * **Solution**: Instead of `.click(fn)` use `.on("click", fn)`. Instead of `.click()` use `.trigger("click")`.
     */
    resize<TData>(eventData: TData,
                  handler: JQuery.TypeEventHandler<TElement, TData, TElement, TElement, 'resize'>): this;
    /**
     * Bind an event handler to the "resize" JavaScript event, or trigger that event on an element.
     * @param handler A function to execute each time the event is triggered.
     * @see \`{@link https://api.jquery.com/resize/ }\`
     * @since 1.0
     * @deprecated ​ Deprecated since 3.3. Use \`{@link on }\` or \`{@link trigger }\`.
     *
     * **Cause**: The `.on()` and `.trigger()` methods can set an event handler or generate an event for any event type, and should be used instead of the shortcut methods. This message also applies to the other event shorthands, including: blur, focus, focusin, focusout, resize, scroll, dblclick, mousedown, mouseup, mousemove, mouseover, mouseout, mouseenter, mouseleave, change, select, submit, keydown, keypress, keyup, and contextmenu.
     *
     * **Solution**: Instead of `.click(fn)` use `.on("click", fn)`. Instead of `.click()` use `.trigger("click")`.
     * @example ​ ````To see the window width while (or after) it is resized, try:
```javascript
$( window ).resize(function() {
  $( "body" ).prepend( "<div>" + $( window ).width() + "</div>" );
});
```
     */
    resize(handler?: JQuery.TypeEventHandler<TElement, null, TElement, TElement, 'resize'> |
                     false): this;
    /**
     * Bind an event handler to the "scroll" JavaScript event, or trigger that event on an element.
     * @param eventData An object containing data that will be passed to the event handler.
     * @param handler A function to execute each time the event is triggered.
     * @see \`{@link https://api.jquery.com/scroll/ }\`
     * @since 1.4.3
     * @deprecated ​ Deprecated since 3.3. Use \`{@link on }\` or \`{@link trigger }\`.
     *
     * **Cause**: The `.on()` and `.trigger()` methods can set an event handler or generate an event for any event type, and should be used instead of the shortcut methods. This message also applies to the other event shorthands, including: blur, focus, focusin, focusout, resize, scroll, dblclick, mousedown, mouseup, mousemove, mouseover, mouseout, mouseenter, mouseleave, change, select, submit, keydown, keypress, keyup, and contextmenu.
     *
     * **Solution**: Instead of `.click(fn)` use `.on("click", fn)`. Instead of `.click()` use `.trigger("click")`.
     */
    scroll<TData>(eventData: TData,
                  handler: JQuery.TypeEventHandler<TElement, TData, TElement, TElement, 'scroll'>): this;
    /**
     * Bind an event handler to the "scroll" JavaScript event, or trigger that event on an element.
     * @param handler A function to execute each time the event is triggered.
     * @see \`{@link https://api.jquery.com/scroll/ }\`
     * @since 1.0
     * @deprecated ​ Deprecated since 3.3. Use \`{@link on }\` or \`{@link trigger }\`.
     *
     * **Cause**: The `.on()` and `.trigger()` methods can set an event handler or generate an event for any event type, and should be used instead of the shortcut methods. This message also applies to the other event shorthands, including: blur, focus, focusin, focusout, resize, scroll, dblclick, mousedown, mouseup, mousemove, mouseover, mouseout, mouseenter, mouseleave, change, select, submit, keydown, keypress, keyup, and contextmenu.
     *
     * **Solution**: Instead of `.click(fn)` use `.on("click", fn)`. Instead of `.click()` use `.trigger("click")`.
     * @example ​ ````To do something when your page is scrolled:
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>scroll demo</title>
  <style>
  div {
    color: blue;
  }
  p {
    color: green;
  }
  span {
    color: red;
    display: none;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<div>Try scrolling the iframe.</div>
<p>Paragraph - <span>Scroll happened!</span></p>
​
<script>
$( "p" ).clone().appendTo( document.body );
$( "p" ).clone().appendTo( document.body );
$( "p" ).clone().appendTo( document.body );
$( window ).scroll(function() {
  $( "span" ).css( "display", "inline" ).fadeOut( "slow" );
});
</script>
​
</body>
</html>
```
     */
    scroll(handler?: JQuery.TypeEventHandler<TElement, null, TElement, TElement, 'scroll'> |
                     false): this;
    /**
     * Set the current horizontal position of the scroll bar for each of the set of matched elements.
     * @param value An integer indicating the new position to set the scroll bar to.
     * @see \`{@link https://api.jquery.com/scrollLeft/ }\`
     * @since 1.2.6
     * @example ​ ````Set the scrollLeft of a div.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>scrollLeft demo</title>
  <style>
  div.demo {
    background: #ccc none repeat scroll 0 0;
    border: 3px solid #666;
    margin: 5px;
    padding: 5px;
    position: relative;
    width: 200px;
    height: 100px;
    overflow: auto;
  }
  p {
    margin: 10px;
    padding: 5px;
    border: 2px solid #666;
    width: 1000px;
    height: 1000px;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<div class="demo"><h1>lalala</h1><p>Hello</p></div>
​
<script>
$( "div.demo" ).scrollLeft( 300 );
</script>
​
</body>
</html>
```
     */
    scrollLeft(value: number): this;
    /**
     * Get the current horizontal position of the scroll bar for the first element in the set of matched elements.
     * @see \`{@link https://api.jquery.com/scrollLeft/ }\`
     * @since 1.2.6
     * @example ​ ````Get the scrollLeft of a paragraph.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>scrollLeft demo</title>
  <style>
  p {
    margin: 10px;
    padding: 5px;
    border: 2px solid #666;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p>Hello</p><p></p>
​
<script>
var p = $( "p:first" );
$( "p:last" ).text( "scrollLeft:" + p.scrollLeft() );
</script>
​
</body>
</html>
```
     */
    scrollLeft(): number | undefined;
    /**
     * Set the current vertical position of the scroll bar for each of the set of matched elements.
     * @param value A number indicating the new position to set the scroll bar to.
     * @see \`{@link https://api.jquery.com/scrollTop/ }\`
     * @since 1.2.6
     * @example ​ ````Set the scrollTop of a div.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>scrollTop demo</title>
  <style>
  div.demo {
    background: #ccc none repeat scroll 0 0;
    border: 3px solid #666;
    margin: 5px;
    padding: 5px;
    position: relative;
    width: 200px;
    height: 100px;
    overflow: auto;
  }
  p {
    margin: 10px;
    padding: 5px;
    border: 2px solid #666;
    width: 1000px;
    height: 1000px;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<div class="demo"><h1>lalala</h1><p>Hello</p></div>
​
<script>
$( "div.demo" ).scrollTop( 300 );
</script>
​
</body>
</html>
```
     */
    scrollTop(value: number): this;
    /**
     * Get the current vertical position of the scroll bar for the first element in the set of matched elements or set the vertical position of the scroll bar for every matched element.
     * @see \`{@link https://api.jquery.com/scrollTop/ }\`
     * @since 1.2.6
     * @example ​ ````Get the scrollTop of a paragraph.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>scrollTop demo</title>
  <style>
  p {
    margin: 10px;
    padding: 5px;
    border: 2px solid #666;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p>Hello</p><p></p>
​
<script>
var p = $( "p:first" );
$( "p:last" ).text( "scrollTop:" + p.scrollTop() );
</script>
​
</body>
</html>
```
     */
    scrollTop(): number | undefined;
    /**
     * Bind an event handler to the "select" JavaScript event, or trigger that event on an element.
     * @param eventData An object containing data that will be passed to the event handler.
     * @param handler A function to execute each time the event is triggered.
     * @see \`{@link https://api.jquery.com/select/ }\`
     * @since 1.4.3
     * @deprecated ​ Deprecated since 3.3. Use \`{@link on }\` or \`{@link trigger }\`.
     *
     * **Cause**: The `.on()` and `.trigger()` methods can set an event handler or generate an event for any event type, and should be used instead of the shortcut methods. This message also applies to the other event shorthands, including: blur, focus, focusin, focusout, resize, scroll, dblclick, mousedown, mouseup, mousemove, mouseover, mouseout, mouseenter, mouseleave, change, select, submit, keydown, keypress, keyup, and contextmenu.
     *
     * **Solution**: Instead of `.click(fn)` use `.on("click", fn)`. Instead of `.click()` use `.trigger("click")`.
     */
    select<TData>(eventData: TData,
                  handler: JQuery.TypeEventHandler<TElement, TData, TElement, TElement, 'select'>): this;
    /**
     * Bind an event handler to the "select" JavaScript event, or trigger that event on an element.
     * @param handler A function to execute each time the event is triggered.
     * @see \`{@link https://api.jquery.com/select/ }\`
     * @since 1.0
     * @deprecated ​ Deprecated since 3.3. Use \`{@link on }\` or \`{@link trigger }\`.
     *
     * **Cause**: The `.on()` and `.trigger()` methods can set an event handler or generate an event for any event type, and should be used instead of the shortcut methods. This message also applies to the other event shorthands, including: blur, focus, focusin, focusout, resize, scroll, dblclick, mousedown, mouseup, mousemove, mouseover, mouseout, mouseenter, mouseleave, change, select, submit, keydown, keypress, keyup, and contextmenu.
     *
     * **Solution**: Instead of `.click(fn)` use `.on("click", fn)`. Instead of `.click()` use `.trigger("click")`.
     * @example ​ ````To do something when text in input boxes is selected:
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>select demo</title>
  <style>
  p {
    color: blue;
  }
  div {
    color: red;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
  <p>Click and drag the mouse to select text in the inputs.</p>
  <input type="text" value="Some text">
  <input type="text" value="to test on">
  <div></div>
  ​
<script>
$( ":input" ).select(function() {
  $( "div" ).text( "Something was selected" ).show().fadeOut( 1000 );
});
</script>
​
</body>
</html>
```
     * @example ​ ````To trigger the select event on all input elements, try:
```javascript
$( "input" ).select();
```
     */
    select(handler?: JQuery.TypeEventHandler<TElement, null, TElement, TElement, 'select'> |
                     false): this;
    /**
     * Encode a set of form elements as a string for submission.
     * @see \`{@link https://api.jquery.com/serialize/ }\`
     * @since 1.0
     * @example ​ ````Serialize a form to a query string that could be sent to a server in an Ajax request.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>serialize demo</title>
  <style>
  body, select {
    font-size: 12px;
  }
  form {
    margin: 5px;
  }
  p {
    color: red;
    margin: 5px;
    font-size: 14px;
  }
  b {
    color: blue;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<form>
  <select name="single">
    <option>Single</option>
    <option>Single2</option>
  </select>
​
  <br>
  <select name="multiple" multiple="multiple">
    <option selected="selected">Multiple</option>
    <option>Multiple2</option>
    <option selected="selected">Multiple3</option>
  </select>
​
  <br>
  <input type="checkbox" name="check" value="check1" id="ch1">
  <label for="ch1">check1</label>
  <input type="checkbox" name="check" value="check2" checked="checked" id="ch2">
  <label for="ch2">check2</label>
​
  <br>
  <input type="radio" name="radio" value="radio1" checked="checked" id="r1">
  <label for="r1">radio1</label>
  <input type="radio" name="radio" value="radio2" id="r2">
  <label for="r2">radio2</label>
</form>
​
<p><tt id="results"></tt></p>
​
<script>
  function showValues() {
    var str = $( "form" ).serialize();
    $( "#results" ).text( str );
  }
  $( "input[type='checkbox'], input[type='radio']" ).on( "click", showValues );
  $( "select" ).on( "change", showValues );
  showValues();
</script>
​
</body>
</html>
```
     */
    serialize(): string;
    /**
     * Encode a set of form elements as an array of names and values.
     * @see \`{@link https://api.jquery.com/serializeArray/ }\`
     * @since 1.2
     * @example ​ ````Get the values from a form, iterate through them, and append them to a results display.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>serializeArray demo</title>
  <style>
  body, select {
    font-size: 14px;
  }
  form {
    margin: 5px;
  }
  p {
    color: red;
    margin: 5px;
  }
  b {
    color: blue;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><b>Results:</b> <span id="results"></span></p>
<form>
  <select name="single">
    <option>Single</option>
    <option>Single2</option>
  </select>
  <select name="multiple" multiple="multiple">
    <option selected="selected">Multiple</option>
    <option>Multiple2</option>
    <option selected="selected">Multiple3</option>
  </select>
  <br>
  <input type="checkbox" name="check" value="check1" id="ch1">
  <label for="ch1">check1</label>
  <input type="checkbox" name="check" value="check2" checked="checked" id="ch2">
  <label for="ch2">check2</label>
  <input type="radio" name="radio" value="radio1" checked="checked" id="r1">
  <label for="r1">radio1</label>
  <input type="radio" name="radio" value="radio2" id="r2">
  <label for="r2">radio2</label>
</form>
​
<script>
  function showValues() {
    var fields = $( ":input" ).serializeArray();
    $( "#results" ).empty();
    jQuery.each( fields, function( i, field ) {
      $( "#results" ).append( field.value + " " );
    });
  }
​
  $( ":checkbox, :radio" ).click( showValues );
  $( "select" ).change( showValues );
  showValues();
</script>
​
</body>
</html>
```
     */
    serializeArray(): JQuery.NameValuePair[];
    /**
     * Display the matched elements.
     * @param duration A string or number determining how long the animation will run.
     * @param easing A string indicating which easing function to use for the transition.
     * @param complete A function to call once the animation is complete, called once per matched element.
     * @see \`{@link https://api.jquery.com/show/ }\`
     * @since 1.4.3
     */
    show(duration: JQuery.Duration, easing: string, complete: (this: TElement) => void): this;
    /**
     * Display the matched elements.
     * @param duration A string or number determining how long the animation will run.
     * @param easing_complete _&#x40;param_ `easing_complete`
     * <br>
     * * `easing` — A string indicating which easing function to use for the transition. <br>
     * * `complete` — A function to call once the animation is complete, called once per matched element.
     * @see \`{@link https://api.jquery.com/show/ }\`
     * @since 1.0
     * @since 1.4.3
     * @example ​ ````Show the first div, followed by each next adjacent sibling div in order, with a 200ms animation. Each animation starts when the previous sibling div&#39;s animation ends.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>show demo</title>
  <style>
  div {
    background: #def3ca;
    margin: 3px;
    width: 80px;
    display: none;
    float: left;
    text-align: center;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<button id="showr">Show</button>
<button id="hidr">Hide</button>
<div>Hello 3,</div>
<div>how</div>
<div>are</div>
<div>you?</div>
​
<script>
$( "#showr" ).click(function() {
  $( "div" ).first().show( "fast", function showNext() {
    $( this ).next( "div" ).show( "fast", showNext );
  });
});
​
$( "#hidr" ).click(function() {
  $( "div" ).hide( 1000 );
});
</script>
​
</body>
</html>
```
     * @example ​ ````Show all span and input elements with an animation. Change the text once the animation is done.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>show demo</title>
  <style>
  span {
    display: none;
  }
  div {
    display: none;
  }
  p {
    font-weight: bold;
    background-color: #fcd;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<button>Do it!</button>
<span>Are you sure? (type 'yes' if you are) </span>
<div>
  <form>
    <input type="text"  value="as;ldkfjalsdf">
  </form>
</div>
<p style="display:none;">I'm hidden...</p>
​
<script>
function doIt() {
  $( "span,div" ).show( "slow" );
}
// Can pass in function name
$( "button" ).click( doIt );
​
$( "form" ).submit(function( event ) {
  if ( $( "input" ).val() === "yes" ) {
    $( "p" ).show( 4000, function() {
      $( this ).text( "Ok, DONE! (now showing)" );
    });
  }
  $( "span,div" ).hide( "fast" );
​
  // Prevent form submission
  event.preventDefault();
});
</script>
​
</body>
</html>
```
     */
    show(duration: JQuery.Duration, easing_complete: string | ((this: TElement) => void)): this;
    /**
     * Display the matched elements.
     * @param duration_complete_options _&#x40;param_ `duration_complete_options`
     * <br>
     * * `duration` — A string or number determining how long the animation will run. <br>
     * * `complete` — A function to call once the animation is complete, called once per matched element. <br>
     * * `options` — A map of additional options to pass to the method.
     * @see \`{@link https://api.jquery.com/show/ }\`
     * @since 1.0
     * @example ​ ````Animates all hidden paragraphs to show slowly, completing the animation within 600 milliseconds.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>show demo</title>
  <style>
  p {
    background: yellow;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<button>Show it</button>
<p style="display: none">Hello  2</p>
​
<script>
$( "button" ).click(function() {
  $( "p" ).show( "slow" );
});
</script>
​
</body>
</html>
```
     */
    show(duration_complete_options?: JQuery.Duration | ((this: TElement) => void) | JQuery.EffectsOptions<TElement>): this;
    /**
     * Get the siblings of each element in the set of matched elements, optionally filtered by a selector.
     * @param selector A string containing a selector expression to match elements against.
     * @see \`{@link https://api.jquery.com/siblings/ }\`
     * @since 1.0
     * @example ​ ````Find the unique siblings of all yellow li elements in the 3 lists (including other yellow li elements if appropriate).
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>siblings demo</title>
  <style>
  ul {
    float: left;
    margin: 5px;
    font-size: 16px;
    font-weight: bold;
  }
  p {
    color: blue;
    margin: 10px 20px;
    font-size: 16px;
    padding: 5px;
    font-weight: bolder;
  }
  .hilite {
    background: yellow;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<ul>
  <li>One</li>
  <li>Two</li>
  <li class="hilite">Three</li>
  <li>Four</li>
</ul>
​
<ul>
  <li>Five</li>
  <li>Six</li>
  <li>Seven</li>
</ul>
​
<ul>
  <li>Eight</li>
  <li class="hilite">Nine</li>
  <li>Ten</li>
  <li class="hilite">Eleven</li>
</ul>
​
<p>Unique siblings: <b></b></p>
​
<script>
var len = $( ".hilite" ).siblings()
  .css( "color", "red" )
  .length;
$( "b" ).text( len );
</script>
​
</body>
</html>
```
     * @example ​ ````Find all siblings with a class &quot;selected&quot; of each div.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>siblings demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<div><span>Hello</span></div>
<p class="selected">Hello Again</p>
<p>And Again</p>
​
<script>
$( "p" ).siblings( ".selected" ).css( "background", "yellow" );
</script>
​
</body>
</html>
```
     */
    siblings(selector?: JQuery.Selector): this;
    /**
     * Reduce the set of matched elements to a subset specified by a range of indices.
     * @param start An integer indicating the 0-based position at which the elements begin to be selected. If negative,
     *              it indicates an offset from the end of the set.
     * @param end An integer indicating the 0-based position at which the elements stop being selected. If negative,
     *            it indicates an offset from the end of the set. If omitted, the range continues until the end of the set.
     * @see \`{@link https://api.jquery.com/slice/ }\`
     * @since 1.1.4
     * @example ​ ````Turns divs yellow based on a random slice.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>slice demo</title>
  <style>
  div {
    width: 40px;
    height: 40px;
    margin: 10px;
    float: left;
    border: 2px solid blue;
  }
  span {
    color: red;
    font-weight: bold;
  }
  button {
    margin: 5px;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><button>Turn slice yellow</button>
  <span>Click the button!</span></p>
  <div></div>
  <div></div>
  <div></div>
  <div></div>
  <div></div>
  <div></div>
  <div></div>
  <div></div>
  <div></div>
  ​
<script>
function colorEm() {
  var $div = $( "div" );
  var start = Math.floor( Math.random() * $div.length );
  var end = Math.floor( Math.random() * ( $div.length - start ) ) +
    start + 1;
  if ( end === $div.length ) {
    end = undefined;
  }
  $div.css( "background", "" );
  if ( end ) {
    $div.slice( start, end ).css( "background", "yellow" );
  } else {
    $div.slice( start ).css( "background", "yellow" );
  }
  $( "span" ).text( "$( 'div' ).slice( " + start +
    (end ? ", " + end : "") +
    ").css( 'background', 'yellow' );" );
}
​
$( "button" ).click( colorEm );
</script>
​
</body>
</html>
```
     * @example ​ ````Selects all paragraphs, then slices the selection to include only the first element.
```javascript
$( "p" ).slice( 0, 1 ).wrapInner( "<b></b>" );
```
     * @example ​ ````Selects all paragraphs, then slices the selection to include only the first and second element.
```javascript
$( "p" ).slice( 0, 2 ).wrapInner( "<b></b>" );
```
     * @example ​ ````Selects all paragraphs, then slices the selection to include only the second element.
```javascript
$( "p" ).slice( 1, 2 ).wrapInner( "<b></b>" );
```
     * @example ​ ````Selects all paragraphs, then slices the selection to include only the second and third element.
```javascript
$( "p" ).slice( 1 ).wrapInner( "<b></b>" );
```
     * @example ​ ````Selects all paragraphs, then slices the selection to include only the third element.
```javascript
$( "p" ).slice( -1 ).wrapInner( "<b></b>" );
```
     */
    slice(start: number, end?: number): this;
    /**
     * Display the matched elements with a sliding motion.
     * @param duration A string or number determining how long the animation will run.
     * @param easing A string indicating which easing function to use for the transition.
     * @param complete A function to call once the animation is complete, called once per matched element.
     * @see \`{@link https://api.jquery.com/slideDown/ }\`
     * @since 1.4.3
     */
    slideDown(duration: JQuery.Duration, easing: string, complete?: (this: TElement) => void): this;
    /**
     * Display the matched elements with a sliding motion.
     * @param duration_easing _&#x40;param_ `duration_easing`
     * <br>
     * * `duration` — A string or number determining how long the animation will run. <br>
     * * `easing` — A string indicating which easing function to use for the transition.
     * @param complete A function to call once the animation is complete, called once per matched element.
     * @see \`{@link https://api.jquery.com/slideDown/ }\`
     * @since 1.0
     * @since 1.4.3
     * @example ​ ````Animates all inputs to slide down, completing the animation within 1000 milliseconds. Once the animation is done, the input look is changed especially if it is the middle input which gets the focus.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>slideDown demo</title>
  <style>
  div {
    background: #cfd;
    margin: 3px;
    width: 50px;
    text-align: center;
    float: left;
    cursor: pointer;
    border: 2px outset black;
    font-weight: bolder;
  }
  input {
    display: none;
    width: 120px;
    float: left;
    margin: 10px;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<div>Push!</div>
<input type="text">
<input type="text" class="middle">
<input type="text">
  ​
<script>
$( "div" ).click(function() {
  $( this ).css({
    borderStyle: "inset",
    cursor: "wait"
  });
  $( "input" ).slideDown( 1000, function() {
    $( this )
      .css( "border", "2px red inset" )
      .filter( ".middle" )
        .css( "background", "yellow" )
        .focus();
    $( "div" ).css( "visibility", "hidden" );
  });
});
​
</script>
​
</body>
</html>
```
     */
    slideDown(duration_easing: JQuery.Duration | string, complete: (this: TElement) => void): this;
    /**
     * Display the matched elements with a sliding motion.
     * @param duration_easing_complete_options _&#x40;param_ `duration_easing_complete_options`
     * <br>
     * * `duration` — A string or number determining how long the animation will run. <br>
     * * `easing` — A string indicating which easing function to use for the transition. <br>
     * * `complete` — A function to call once the animation is complete, called once per matched element. <br>
     * * `options` — A map of additional options to pass to the method.
     * @see \`{@link https://api.jquery.com/slideDown/ }\`
     * @since 1.0
     * @since 1.4.3
     * @example ​ ````Animates all divs to slide down and show themselves over 600 milliseconds.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>slideDown demo</title>
  <style>
  div {
    background: #de9a44;
    margin: 3px;
    width: 80px;
    height: 40px;
    display: none;
    float: left;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
Click me!
<div></div>
<div></div>
<div></div>
​
<script>
$( document.body ).click(function () {
  if ( $( "div:first" ).is( ":hidden" ) ) {
    $( "div" ).slideDown( "slow" );
  } else {
    $( "div" ).hide();
  }
});
</script>
​
</body>
</html>
```
     */
    slideDown(duration_easing_complete_options?: JQuery.Duration | string | ((this: TElement) => void) | JQuery.EffectsOptions<TElement>): this;
    /**
     * Display or hide the matched elements with a sliding motion.
     * @param duration A string or number determining how long the animation will run.
     * @param easing A string indicating which easing function to use for the transition.
     * @param complete A function to call once the animation is complete, called once per matched element.
     * @see \`{@link https://api.jquery.com/slideToggle/ }\`
     * @since 1.4.3
     */
    slideToggle(duration: JQuery.Duration, easing: string, complete?: (this: TElement) => void): this;
    /**
     * Display or hide the matched elements with a sliding motion.
     * @param duration_easing _&#x40;param_ `duration_easing`
     * <br>
     * * `duration` — A string or number determining how long the animation will run. <br>
     * * `easing` — A string indicating which easing function to use for the transition.
     * @param complete A function to call once the animation is complete, called once per matched element.
     * @see \`{@link https://api.jquery.com/slideToggle/ }\`
     * @since 1.0
     * @since 1.4.3
     * @example ​ ````Animates divs between dividers with a toggle that makes some appear and some disappear.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>slideToggle demo</title>
  <style>
  div {
    background: #b977d1;
    margin: 3px;
    width: 60px;
    height: 60px;
    float: left;
  }
  div.still {
    background: #345;
    width: 5px;
  }
  div.hider {
    display: none;
  }
  span {
    color: red;
  }
  p {
    clear: left;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<div></div>
<div class="still"></div>
<div style="display:none;">
</div><div class="still"></div>
<div></div>
<div class="still"></div>
<div class="hider"></div>
<div class="still"></div>
<div class="hider"></div>
<div class="still"></div>
<div></div>
<p><button id="aa">Toggle</button> There have been <span>0</span> toggled divs.</p>
​
<script>
$( "#aa" ).click(function() {
  $( "div:not(.still)" ).slideToggle( "slow", function() {
    var n = parseInt( $( "span" ).text(), 10 );
    $( "span" ).text( n + 1 );
  });
});
</script>
​
</body>
</html>
```
     */
    slideToggle(duration_easing: JQuery.Duration | string, complete: (this: TElement) => void): this;
    /**
     * Display or hide the matched elements with a sliding motion.
     * @param duration_easing_complete_options _&#x40;param_ `duration_easing_complete_options`
     * <br>
     * * `duration` — A string or number determining how long the animation will run. <br>
     * * `easing` — A string indicating which easing function to use for the transition. <br>
     * * `complete` — A function to call once the animation is complete, called once per matched element. <br>
     * * `options` — A map of additional options to pass to the method.
     * @see \`{@link https://api.jquery.com/slideToggle/ }\`
     * @since 1.0
     * @since 1.4.3
     * @example ​ ````Animates all paragraphs to slide up or down, completing the animation within 600 milliseconds.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>slideToggle demo</title>
  <style>
  p {
    width: 400px;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<button>Toggle</button>
<p>
  This is the paragraph to end all paragraphs.  You
  should feel <em>lucky</em> to have seen such a paragraph in
  your life.  Congratulations!
</p>
​
<script>
$( "button" ).click(function() {
  $( "p" ).slideToggle( "slow" );
});
</script>
​
</body>
</html>
```
     */
    slideToggle(duration_easing_complete_options?: JQuery.Duration | string | ((this: TElement) => void) | JQuery.EffectsOptions<TElement>): this;
    /**
     * Hide the matched elements with a sliding motion.
     * @param duration A string or number determining how long the animation will run.
     * @param easing A string indicating which easing function to use for the transition.
     * @param complete A function to call once the animation is complete, called once per matched element.
     * @see \`{@link https://api.jquery.com/slideUp/ }\`
     * @since 1.4.3
     */
    slideUp(duration: JQuery.Duration, easing: string, complete?: (this: TElement) => void): this;
    /**
     * Hide the matched elements with a sliding motion.
     * @param duration_easing _&#x40;param_ `duration_easing`
     * <br>
     * * `duration` — A string or number determining how long the animation will run. <br>
     * * `easing` — A string indicating which easing function to use for the transition.
     * @param complete A function to call once the animation is complete, called once per matched element.
     * @see \`{@link https://api.jquery.com/slideUp/ }\`
     * @since 1.0
     * @since 1.4.3
     * @example ​ ````Animates the parent paragraph to slide up, completing the animation within 200 milliseconds. Once the animation is done, it displays an alert.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>slideUp demo</title>
  <style>
 div {
   margin: 2px;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<div>
  <button>Hide One</button>
  <input type="text" value="One">
</div>
​
<div>
  <button>Hide Two</button>
  <input type="text" value="Two">
</div>
​
<div>
  <button>Hide Three</button>
  <input type="text" value="Three">
</div>
​
<div id="msg"></div>
​
<script>
$( "button" ).click(function() {
  $( this ).parent().slideUp( "slow", function() {
    $( "#msg" ).text( $( "button", this ).text() + " has completed." );
  });
});
</script>
​
</body>
</html>
```
     */
    slideUp(duration_easing: JQuery.Duration | string, complete: (this: TElement) => void): this;
    /**
     * Hide the matched elements with a sliding motion.
     * @param duration_easing_complete_options _&#x40;param_ `duration_easing_complete_options`
     * <br>
     * * `duration` — A string or number determining how long the animation will run. <br>
     * * `easing` — A string indicating which easing function to use for the transition. <br>
     * * `complete` — A function to call once the animation is complete, called once per matched element. <br>
     * * `options` — A map of additional options to pass to the method.
     * @see \`{@link https://api.jquery.com/slideUp/ }\`
     * @since 1.0
     * @since 1.4.3
     * @example ​ ````Animates all divs to slide up, completing the animation within 400 milliseconds.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>slideUp demo</title>
  <style>
  div {
    background: #3d9a44;
    margin: 3px;
    width: 80px;
    height: 40px;
    float: left;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
Click me!
<div></div>
<div></div>
<div></div>
<div></div>
<div></div>
​
<script>
$( document.body ).click(function() {
  if ( $( "div:first" ).is( ":hidden" ) ) {
    $( "div" ).show( "slow" );
  } else {
    $( "div" ).slideUp();
  }
});
</script>
​
</body>
</html>
```
     */
    slideUp(duration_easing_complete_options?: JQuery.Duration | string | ((this: TElement) => void) | JQuery.EffectsOptions<TElement>): this;
    /**
     * Stop the currently-running animation on the matched elements.
     * @param queue The name of the queue in which to stop animations.
     * @param clearQueue A Boolean indicating whether to remove queued animation as well. Defaults to false.
     * @param jumpToEnd A Boolean indicating whether to complete the current animation immediately. Defaults to false.
     * @see \`{@link https://api.jquery.com/stop/ }\`
     * @since 1.7
     */
    stop(queue: string, clearQueue?: boolean, jumpToEnd?: boolean): this;
    /**
     * Stop the currently-running animation on the matched elements.
     * @param clearQueue A Boolean indicating whether to remove queued animation as well. Defaults to false.
     * @param jumpToEnd A Boolean indicating whether to complete the current animation immediately. Defaults to false.
     * @see \`{@link https://api.jquery.com/stop/ }\`
     * @since 1.2
     * @example ​ ````Click the Go button once to start the animation, then click the STOP button to stop it where it&#39;s currently positioned.  Another option is to click several buttons to queue them up and see that stop just kills the currently playing one.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>stop demo</title>
  <style>
  div {
    position: absolute;
    background-color: #abc;
    left: 0px;
    top: 30px;
    width: 60px;
    height: 60px;
    margin: 5px;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<button id="go">Go</button>
<button id="stop">STOP!</button>
<button id="back">Back</button>
<div class="block"></div>
​
<script>
// Start animation
$( "#go" ).click(function() {
  $( ".block" ).animate({ left: "+=100px" }, 2000 );
});
​
// Stop animation when button is clicked
$( "#stop" ).click(function() {
  $( ".block" ).stop();
});
​
// Start animation in the opposite direction
$( "#back" ).click(function() {
  $( ".block" ).animate({ left: "-=100px" }, 2000 );
});
</script>
​
</body>
</html>
```
     * @example ​ ````Click the slideToggle button to start the animation, then click again before the animation is completed. The animation will toggle the other direction from the saved starting point.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>stop demo</title>
  <style>
  .block {
    background-color: #abc;
    border: 2px solid black;
    width: 200px;
    height: 80px;
    margin: 10px;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<button id="toggle">slideToggle</button>
<div class="block"></div>
​
<script>
var $block = $( ".block" );
​
// Toggle a sliding animation animation
$( "#toggle" ).on( "click", function() {
  $block.stop().slideToggle( 1000 );
});
</script>
​
</body>
</html>
```
     */
    stop(clearQueue?: boolean, jumpToEnd?: boolean): this;
    /**
     * Bind an event handler to the "submit" JavaScript event, or trigger that event on an element.
     * @param eventData An object containing data that will be passed to the event handler.
     * @param handler A function to execute each time the event is triggered.
     * @see \`{@link https://api.jquery.com/submit/ }\`
     * @since 1.4.3
     * @deprecated ​ Deprecated since 3.3. Use \`{@link on }\` or \`{@link trigger }\`.
     *
     * **Cause**: The `.on()` and `.trigger()` methods can set an event handler or generate an event for any event type, and should be used instead of the shortcut methods. This message also applies to the other event shorthands, including: blur, focus, focusin, focusout, resize, scroll, dblclick, mousedown, mouseup, mousemove, mouseover, mouseout, mouseenter, mouseleave, change, select, submit, keydown, keypress, keyup, and contextmenu.
     *
     * **Solution**: Instead of `.click(fn)` use `.on("click", fn)`. Instead of `.click()` use `.trigger("click")`.
     */
    submit<TData>(eventData: TData,
                  handler: JQuery.TypeEventHandler<TElement, TData, TElement, TElement, 'submit'>): this;
    /**
     * Bind an event handler to the "submit" JavaScript event, or trigger that event on an element.
     * @param handler A function to execute each time the event is triggered.
     * @see \`{@link https://api.jquery.com/submit/ }\`
     * @since 1.0
     * @deprecated ​ Deprecated since 3.3. Use \`{@link on }\` or \`{@link trigger }\`.
     *
     * **Cause**: The `.on()` and `.trigger()` methods can set an event handler or generate an event for any event type, and should be used instead of the shortcut methods. This message also applies to the other event shorthands, including: blur, focus, focusin, focusout, resize, scroll, dblclick, mousedown, mouseup, mousemove, mouseover, mouseout, mouseenter, mouseleave, change, select, submit, keydown, keypress, keyup, and contextmenu.
     *
     * **Solution**: Instead of `.click(fn)` use `.on("click", fn)`. Instead of `.click()` use `.trigger("click")`.
     * @example ​ ````If you&#39;d like to prevent forms from being submitted unless a flag variable is set, try:
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>submit demo</title>
  <style>
  p {
    margin: 0;
    color: blue;
  }
  div,p {
    margin-left: 10px;
  }
  span {
    color: red;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p>Type 'correct' to validate.</p>
<form action="javascript:alert( 'success!' );">
  <div>
    <input type="text">
    <input type="submit">
  </div>
</form>
<span></span>
​
<script>
$( "form" ).submit(function( event ) {
  if ( $( "input:first" ).val() === "correct" ) {
    $( "span" ).text( "Validated..." ).show();
    return;
  }
​
  $( "span" ).text( "Not valid!" ).show().fadeOut( 1000 );
  event.preventDefault();
});
</script>
​
</body>
</html>
```
     * @example ​ ````If you&#39;d like to prevent forms from being submitted unless a flag variable is set, try:
```javascript
$( "form" ).submit(function() {
  return this.some_flag_variable;
});
```
     * @example ​ ````To trigger the submit event on the first form on the page, try:
```javascript
$( "form:first" ).submit();
```
     */
    submit(handler?: JQuery.TypeEventHandler<TElement, null, TElement, TElement, 'submit'> |
                     false): this;
    /**
     * Set the content of each element in the set of matched elements to the specified text.
     * @param text_function _&#x40;param_ `text_function`
     * <br>
     * * `text` — The text to set as the content of each matched element. When Number or Boolean is supplied, it will
     *            be converted to a String representation. <br>
     * * `function` — A function returning the text content to set. Receives the index position of the element in the set
     *                and the old text value as arguments.
     * @see \`{@link https://api.jquery.com/text/ }\`
     * @since 1.0
     * @since 1.4
     * @example ​ ````Add text to the paragraph (notice the bold tag is escaped).
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>text demo</title>
  <style>
  p {
    color: blue;
    margin: 8px;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p>Test Paragraph.</p>
​
<script>
$( "p" ).text( "<b>Some</b> new text." );
</script>
​
</body>
</html>
```
     */
    text(text_function: string | number | boolean | ((this: TElement, index: number, text: string) => string | number | boolean)): this;
    /**
     * Get the combined text contents of each element in the set of matched elements, including their descendants.
     * @see \`{@link https://api.jquery.com/text/ }\`
     * @since 1.0
     * @example ​ ````Find the text in the first paragraph (stripping out the html), then set the html of the last paragraph to show it is just text (the red bold is gone).
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>text demo</title>
  <style>
  p {
    color: blue;
    margin: 8px;
  }
  b {
    color: red;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><b>Test</b> Paragraph.</p>
<p></p>
​
<script>
var str = $( "p:first" ).text();
$( "p:last" ).html( str );
</script>
​
</body>
</html>
```
     */
    text(): string;
    /**
     * Retrieve all the elements contained in the jQuery set, as an array.
     * @see \`{@link https://api.jquery.com/toArray/ }\`
     * @since 1.4
     * @example ​ ````Select all divs in the document and return the DOM Elements as an Array; then use the built-in reverse() method to reverse that array.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>toArray demo</title>
  <style>
  span {
    color: red;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
Reversed - <span></span>
​
<div>One</div>
<div>Two</div>
<div>Three</div>​
<script>
function disp( divs ) {
  var a = [];
  for ( var i = 0; i < divs.length; i++ ) {
    a.push( divs[ i ].innerHTML );
  }
  $( "span" ).text( a.join( " " ) );
}
​
disp( $( "div" ).toArray().reverse() );
</script>
​
</body>
</html>
```
     */
    toArray(): TElement[];
    /**
     * Display or hide the matched elements.
     * @param duration A string or number determining how long the animation will run.
     * @param easing A string indicating which easing function to use for the transition.
     * @param complete A function to call once the animation is complete, called once per matched element.
     * @see \`{@link https://api.jquery.com/toggle/ }\`
     * @since 1.4.3
     */
    toggle(duration: JQuery.Duration, easing: string, complete?: (this: TElement) => void): this;
    /**
     * Display or hide the matched elements.
     * @param duration A string or number determining how long the animation will run.
     * @param complete A function to call once the animation is complete, called once per matched element.
     * @see \`{@link https://api.jquery.com/toggle/ }\`
     * @since 1.0
     */
    toggle(duration: JQuery.Duration, complete: (this: TElement) => void): this;
    /**
     * Display or hide the matched elements.
     * @param duration_complete_options_display _&#x40;param_ `duration_complete_options_display`
     * <br>
     * * `duration` — A string or number determining how long the animation will run. <br>
     * * `complete` — A function to call once the animation is complete, called once per matched element. <br>
     * * `options` — A map of additional options to pass to the method. <br>
     * * `display` — Use true to show the element or false to hide it.
     * @see \`{@link https://api.jquery.com/toggle/ }\`
     * @since 1.0
     * @since 1.3
     * @example ​ ````Toggles all paragraphs.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>toggle demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<button>Toggle</button>
<p>Hello</p>
<p style="display: none">Good Bye</p>
​
<script>
$( "button" ).click(function() {
  $( "p" ).toggle();
});
</script>
​
</body>
</html>
```
     * @example ​ ````Animates all paragraphs to be shown if they are hidden and hidden if they are visible, completing the animation within 600 milliseconds.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>toggle demo</title>
  <style>
  p {
    background: #dad;
    font-weight: bold;
    font-size: 16px;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<button>Toggle 'em</button>
<p>Hiya</p>
<p>Such interesting text, eh?</p>
​
<script>
$( "button" ).click(function() {
  $( "p" ).toggle( "slow" );
});
</script>
​
</body>
</html>
```
     * @example ​ ````Shows all paragraphs, then hides them all, back and forth.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>toggle demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<button>Toggle</button>
<p>Hello</p>
<p style="display: none">Good Bye</p>
​
<script>
var flip = 0;
$( "button" ).click(function() {
  $( "p" ).toggle( flip++ % 2 === 0 );
});
</script>
​
</body>
</html>
```
     */
    toggle(duration_complete_options_display?: JQuery.Duration | ((this: TElement) => void) | JQuery.EffectsOptions<TElement> | boolean): this;
    /**
     * Add or remove one or more classes from each element in the set of matched elements, depending on either the class's presence or the value of the state argument.
     * @param className_function _&#x40;param_ `className_function`
     * <br>
     * * `className` — One or more class names (separated by spaces) to be toggled for each element in the matched set. <br>
     * * `function` — A function that returns class names to be toggled in the class attribute of each element in the
     *                matched set. Receives the index position of the element in the set, the old class value, and the state as arguments.
     * @param state A Boolean (not just truthy/falsy) value to determine whether the class should be added or removed.
     * @see \`{@link https://api.jquery.com/toggleClass/ }\`
     * @since 1.0
     * @since 1.3
     * @since 1.4
     * @since 3.3
     * @example ​ ````Toggle the class &#39;highlight&#39; when a paragraph is clicked.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>toggleClass demo</title>
  <style>
  p {
    margin: 4px;
    font-size: 16px;
    font-weight: bolder;
    cursor: pointer;
  }
  .blue {
    color: blue;
  }
  .highlight {
    background: yellow;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p class="blue">Click to toggle</p>
<p class="blue highlight">highlight</p>
<p class="blue">on these</p>
<p class="blue">paragraphs</p>
​
<script>
$( "p" ).click(function() {
  $( this ).toggleClass( "highlight" );
});
</script>
​
</body>
</html>
```
     * @example ​ ````Add the &quot;highlight&quot; class to the clicked paragraph on every third click of that paragraph, remove it every first and second click.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>toggleClass demo</title>
  <style>
  p {
    margin: 4px;
    font-size: 16px;
    font-weight: bolder;
    cursor: pointer;
  }
  .blue {
    color: blue;
  }
  .highlight {
    background: red;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p class="blue">Click to toggle (<span>clicks: 0</span>)</p>
<p class="blue highlight">highlight (<span>clicks: 0</span>)</p>
<p class="blue">on these (<span>clicks: 0</span>)</p>
<p class="blue">paragraphs (<span>clicks: 0</span>)</p>
​
<script>
var count = 0;
$( "p" ).each(function() {
  var $thisParagraph = $( this );
  var count = 0;
  $thisParagraph.click(function() {
    count++;
    $thisParagraph.find( "span" ).text( "clicks: " + count );
    $thisParagraph.toggleClass( "highlight", count % 3 === 0 );
  });
});
</script>
​
</body>
</html>
```
     * @example ​ ````Toggle the class name(s) indicated on the buttons for each div.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>toggleClass demo</title>
  <style>
  .wrap > div {
    float: left;
    width: 100px;
    margin: 1em 1em 0 0;
    padding-left: 3px;
    border: 1px solid #abc;
  }
  div.a {
    background-color: aqua;
  }
  div.b {
    background-color: burlywood;
  }
  div.c {
    background-color: cornsilk;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<div class="buttons">
  <button>toggle</button>
  <button class="a">toggle a</button>
  <button class="a b">toggle a b</button>
  <button class="a b c">toggle a b c</button>
  <a href="#">reset</a>
</div>
<div class="wrap">
  <div></div>
  <div class="b"></div>
  <div class="a b"></div>
  <div class="a c"></div>
</div>
​
<script>
var cls = [ "", "a", "a b", "a b c" ];
var divs = $( "div.wrap" ).children();
var appendClass = function() {
  divs.append(function() {
    return "<div>" + ( this.className || "none" ) + "</div>";
  });
};
​
appendClass();
​
$( "button" ).on( "click", function() {
  var tc = this.className || undefined;
  divs.toggleClass( tc );
  appendClass();
});
​
$( "a" ).on( "click", function( event ) {
  event.preventDefault();
  divs.empty().each(function( i ) {
    this.className = cls[ i ];
  });
  appendClass();
});
</script>
​
</body>
</html>
```
     */
    toggleClass<TState extends boolean>(className_function: JQuery.TypeOrArray<string> | ((this: TElement, index: number, className: string, state: TState) => string),
                                        state?: TState): this;
    /**
     * Add or remove one or more classes from each element in the set of matched elements, depending on either the class's presence or the value of the state argument.
     * @param state A boolean value to determine whether the class should be added or removed.
     * @see \`{@link https://api.jquery.com/toggleClass/ }\`
     * @since 1.4
     * @deprecated ​ Deprecated since 3.0. See \`{@link https://github.com/jquery/jquery/pull/2618 }\`.
     *
     * **Cause**: Calling `.toggleClass()` with no arguments, or with a single Boolean `true` or `false` argument, has been deprecated. Its behavior was poorly documented, but essentially the method saved away the current class value in a data item when the class was removed and restored the saved value when it was toggled back. If you do not believe you are specificially trying to use this form of the method, it is possible you are accidentally doing so via an inadvertent undefined value, as `.toggleClass( undefined )` toggles all classes.
     *
     * **Solution**: If this functionality is still needed, save the current full `.attr( "class" )` value in a data item and restore it when required.
     */
    toggleClass(state?: boolean): this;
    /**
     * Execute all handlers and behaviors attached to the matched elements for the given event type.
     * @param eventType_event _&#x40;param_ `eventType_event`
     * <br>
     * * `eventType` — A string containing a JavaScript event type, such as `click` or `submit`. <br>
     * * `event` — A \`{@link https://api.jquery.com/category/events/event-object/ jQuery.Event}\` object.
     * @param extraParameters Additional parameters to pass along to the event handler.
     * @see \`{@link https://api.jquery.com/trigger/ }\`
     * @since 1.0
     * @since 1.3
     * @example ​ ````Clicks to button #2 also trigger a click for button #1.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>trigger demo</title>
  <style>
  button {
    margin: 10px;
  }
  div {
    color: blue;
    font-weight: bold;
  }
  span {
    color: red;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<button>Button #1</button>
<button>Button #2</button>
<div><span>0</span> button #1 clicks.</div>
<div><span>0</span> button #2 clicks.</div>
​
<script>
$( "button:first" ).click(function() {
  update( $( "span:first" ) );
});
​
$( "button:last" ).click(function() {
  $( "button:first" ).trigger( "click" );
  update( $( "span:last" ) );
});
​
function update( j ) {
  var n = parseInt( j.text(), 10 );
  j.text( n + 1 );
}
</script>
​
</body>
</html>
```
     * @example ​ ````To submit the first form without using the submit() function, try:
```javascript
$( "form:first" ).trigger( "submit" );
```
     * @example ​ ````To submit the first form without using the submit() function, try:
```javascript
var event = jQuery.Event( "submit" );
$( "form:first" ).trigger( event );
if ( event.isDefaultPrevented() ) {
  // Perform an action...
}
```
     * @example ​ ````To pass arbitrary data to an event:
```javascript
$( "p" )
  .click(function( event, a, b ) {
    // When a normal click fires, a and b are undefined
    // for a trigger like below a refers to "foo" and b refers to "bar"
  })
  .trigger( "click", [ "foo", "bar" ] );
```
     * @example ​ ````To pass arbitrary data through an event object:
```javascript
var event = jQuery.Event( "logged" );
event.user = "foo";
event.pass = "bar";
$( "body" ).trigger( event );
```
     * @example ​ ````Alternative way to pass data through an event object:
```javascript
$( "body" ).trigger({
  type:"logged",
  user:"foo",
  pass:"bar"
});
```
     */
    trigger(eventType_event: string | JQuery.Event, extraParameters?: any[] | JQuery.PlainObject | string | number | boolean): this;
    /**
     * Execute all handlers attached to an element for an event.
     * @param eventType_event _&#x40;param_ `eventType_event`
     * <br>
     * * `eventType` — A string containing a JavaScript event type, such as `click` or `submit`. <br>
     * * `event` — A \`{@link https://api.jquery.com/category/events/event-object/ jQuery.Event}\` object.
     * @param extraParameters Additional parameters to pass along to the event handler.
     * @see \`{@link https://api.jquery.com/triggerHandler/ }\`
     * @since 1.2
     * @since 1.3
     * @example ​ ````If you called .triggerHandler() on a focus event - the browser&#39;s default focus action would not be triggered, only the event handlers bound to the focus event.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>triggerHandler demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<button id="old">.trigger( "focus" )</button>
<button id="new">.triggerHandler( "focus" )</button><br><br>
​
<input type="text" value="To Be Focused">
​
<script>
$( "#old" ).click(function() {
  $( "input" ).trigger( "focus" );
});
$( "#new" ).click(function() {
  $( "input" ).triggerHandler( "focus" );
});
$( "input" ).focus(function() {
  $( "<span>Focused!</span>" ).appendTo( "body" ).fadeOut( 1000 );
});
</script>
​
</body>
</html>
```
     */
    triggerHandler(eventType_event: string | JQuery.Event, extraParameters?: any[] | JQuery.PlainObject | string | number | boolean): any;
    /**
     * Remove a previously-attached event handler from the elements.
     * @param event A string containing one or more DOM event types, such as "click" or "submit," or custom event names.
     * @param handler A function to execute each time the event is triggered.
     * @see \`{@link https://api.jquery.com/unbind/ }\`
     * @since 1.0
     * @since 1.4.3
     * @deprecated ​ Deprecated since 3.0. Use \`{@link off }\`.
     *
     * **Cause**: These event binding methods have been deprecated in favor of the `.on()` and `.off()` methods which can handle both delegated and direct event binding. Although the older methods are still present in jQuery 3.0, they may be removed as early as the next major-version update.
     *
     * **Solution**: Change the method call to use `.on()` or `.off()`, the documentation for the old methods include specific instructions. In general, the `.bind()` and `.unbind()` methods can be renamed directly to `.on()` and `.off()` respectively since the argument orders are identical.
     * @example ​ ````Can bind and unbind events to the colored button.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>unbind demo</title>
  <style>
  button {
    margin: 5px;
  }
  button#theone {
    color: red;
    background: yellow;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<button id="theone">Does nothing...</button>
<button id="bind">Bind Click</button>
<button id="unbind">Unbind Click</button>
<div style="display:none;">Click!</div>
​
<script>
function aClick() {
  $( "div" ).show().fadeOut( "slow" );
}
$( "#bind" ).click(function() {
  $( "#theone" )
    .bind( "click", aClick )
    .text( "Can Click!" );
});
$( "#unbind" ).click(function() {
  $( "#theone" )
    .unbind( "click", aClick )
    .text( "Does nothing..." );
});
</script>
​
</body>
</html>
```
     * @example ​ ````To unbind just one previously bound handler, pass the function in as the second argument:
```javascript
var foo = function() {
  // Code to handle some kind of event
};
​
$( "p" ).bind( "click", foo ); // ... Now foo will be called when paragraphs are clicked ...
​
$( "p" ).unbind( "click", foo ); // ... foo will no longer be called.
```
     */
    unbind<TType extends string>(
        event: TType,
        handler: JQuery.TypeEventHandler<TElement, any, TElement, TElement, TType> |
                 false
    ): this;
    /**
     * Remove a previously-attached event handler from the elements.
     * @param event A string containing one or more DOM event types, such as "click" or "submit," or custom event names.
     *              A jQuery.Event object.
     * @see \`{@link https://api.jquery.com/unbind/ }\`
     * @since 1.0
     * @deprecated ​ Deprecated since 3.0. Use \`{@link off }\`.
     *
     * **Cause**: These event binding methods have been deprecated in favor of the `.on()` and `.off()` methods which can handle both delegated and direct event binding. Although the older methods are still present in jQuery 3.0, they may be removed as early as the next major-version update.
     *
     * **Solution**: Change the method call to use `.on()` or `.off()`, the documentation for the old methods include specific instructions. In general, the `.bind()` and `.unbind()` methods can be renamed directly to `.on()` and `.off()` respectively since the argument orders are identical.
     * @example ​ ````To unbind all events from all paragraphs, write:
```javascript
$( "p" ).unbind();
```
     * @example ​ ````To unbind all click events from all paragraphs, write:
```javascript
$( "p" ).unbind( "click" );
```
     */
    unbind(event?: string | JQuery.TriggeredEvent<TElement>): this;
    /**
     * Remove a handler from the event for all elements which match the current selector, based upon a specific set of root elements.
     * @param selector A selector which will be used to filter the event results.
     * @param eventType A string containing a JavaScript event type, such as "click" or "keydown"
     * @param handler A function to execute each time the event is triggered.
     * @see \`{@link https://api.jquery.com/undelegate/ }\`
     * @since 1.4.2
     * @deprecated ​ Deprecated since 3.0. Use \`{@link off }\`.
     *
     * **Cause**: These event binding methods have been deprecated in favor of the `.on()` and `.off()` methods which can handle both delegated and direct event binding. Although the older methods are still present in jQuery 3.0, they may be removed as early as the next major-version update.
     *
     * **Solution**: Change the method call to use `.on()` or `.off()`, the documentation for the old methods include specific instructions. In general, the `.bind()` and `.unbind()` methods can be renamed directly to `.on()` and `.off()` respectively since the argument orders are identical.
     * @example ​ ````Can bind and unbind events to the colored button.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>undelegate demo</title>
  <style>
  button {
    margin: 5px;
  }
  button#theone {
    color: red;
    background: yellow;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<button id="theone">Does nothing...</button>
<button id="bind">Bind Click</button>
<button id="unbind">Unbind Click</button>
<div style="display:none;">Click!</div>
​
<script>
function aClick() {
  $( "div" ).show().fadeOut( "slow" );
}
$( "#bind" ).click(function() {
  $( "body" )
    .delegate( "#theone", "click", aClick )
    .find( "#theone" ).text( "Can Click!" );
});
$( "#unbind" ).click(function() {
  $( "body" )
    .undelegate( "#theone", "click", aClick )
    .find( "#theone" ).text( "Does nothing..." );
});
</script>
​
</body>
</html>
```
     * @example ​ ````To undelegate just one previously bound handler, pass the function in as the third argument:
```javascript
var foo = function () {
  // Code to handle some kind of event
};
​
// ... Now foo will be called when paragraphs are clicked ...
$( "body" ).delegate( "p", "click", foo );
​
// ... foo will no longer be called.
$( "body" ).undelegate( "p", "click", foo );
```
     */
    undelegate<TType extends string>(
        selector: JQuery.Selector,
        eventType: TType,
        handler: JQuery.TypeEventHandler<TElement, any, any, any, TType> |
                 false
    ): this;
    /**
     * Remove a handler from the event for all elements which match the current selector, based upon a specific set of root elements.
     * @param selector A selector which will be used to filter the event results.
     * @param eventType_events _&#x40;param_ `eventType_events`
     * <br>
     * * `eventType` — A string containing a JavaScript event type, such as "click" or "keydown" <br>
     * * `events` — An object of one or more event types and previously bound functions to unbind from them.
     * @see \`{@link https://api.jquery.com/undelegate/ }\`
     * @since 1.4.2
     * @since 1.4.3
     * @deprecated ​ Deprecated since 3.0. Use \`{@link off }\`.
     *
     * **Cause**: These event binding methods have been deprecated in favor of the `.on()` and `.off()` methods which can handle both delegated and direct event binding. Although the older methods are still present in jQuery 3.0, they may be removed as early as the next major-version update.
     *
     * **Solution**: Change the method call to use `.on()` or `.off()`, the documentation for the old methods include specific instructions. In general, the `.bind()` and `.unbind()` methods can be renamed directly to `.on()` and `.off()` respectively since the argument orders are identical.
     */
    undelegate(selector: JQuery.Selector,
               eventType_events: string |
                                 JQuery.TypeEventHandlers<TElement, any, any, any>): this;
    /**
     * Remove a handler from the event for all elements which match the current selector, based upon a specific set of root elements.
     * @param namespace A selector which will be used to filter the event results.
     * @see \`{@link https://api.jquery.com/undelegate/ }\`
     * @since 1.4.2
     * @since 1.6
     * @deprecated ​ Deprecated since 3.0. Use \`{@link off }\`.
     *
     * **Cause**: These event binding methods have been deprecated in favor of the `.on()` and `.off()` methods which can handle both delegated and direct event binding. Although the older methods are still present in jQuery 3.0, they may be removed as early as the next major-version update.
     *
     * **Solution**: Change the method call to use `.on()` or `.off()`, the documentation for the old methods include specific instructions. In general, the `.bind()` and `.unbind()` methods can be renamed directly to `.on()` and `.off()` respectively since the argument orders are identical.
     * @example ​ ````To unbind all delegated events from all paragraphs, write:
```javascript
$( "p" ).undelegate();
```
     * @example ​ ````To unbind all delegated click events from all paragraphs, write:
```javascript
$( "p" ).undelegate( "click" );
```
     * @example ​ ````To unbind all delegated events by their namespace:
```javascript
var foo = function() {
  // Code to handle some kind of event
};
​
// Delegate events under the ".whatever" namespace
$( "form" ).delegate( ":button", "click.whatever", foo );
​
$( "form" ).delegate( "input[type='text'] ", "keypress.whatever", foo );
​
// Unbind all events delegated under the ".whatever" namespace
$( "form" ).undelegate( ".whatever" );
```
     */
    undelegate(namespace?: string): this;
    /**
     * Remove the parents of the set of matched elements from the DOM, leaving the matched elements in their place.
     * @param selector A selector to check the parent element against. If an element's parent does not match the selector,
     *                 the element won't be unwrapped.
     * @see \`{@link https://api.jquery.com/unwrap/ }\`
     * @since 1.4
     * @since 3.0
     * @example ​ ````Wrap/unwrap a div around each of the paragraphs.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>unwrap demo</title>
  <style>
  div {
    border: 2px solid blue;
  }
  p {
    background: yellow;
    margin: 4px;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​<button>wrap/unwrap</button>
<p>Hello</p>
<p>cruel</p>
<p>World</p>​
<script>
var pTags = $( "p" );
$( "button" ).click(function() {
  if ( pTags.parent().is( "div" ) ) {
    pTags.unwrap();
  } else {
    pTags.wrap( "<div></div>" );
  }
});
</script>
​
</body>
</html>
```
     */
    unwrap(selector?: string): this;
    /**
     * Set the value of each element in the set of matched elements.
     * @param value_function _&#x40;param_ `value_function`
     * <br>
     * * `value` — A string of text, a number, or an array of strings corresponding to the value of each matched
     *             element to set as selected/checked. <br>
     * * `function` — A function returning the value to set. `this` is the current element. Receives the index position of
     *                the element in the set and the old value as arguments.
     * @see \`{@link https://api.jquery.com/val/ }\`
     * @since 1.0
     * @since 1.4
     * @example ​ ````Set the value of an input box.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>val demo</title>
  <style>
  button {
    margin: 4px;
    cursor: pointer;
  }
  input {
    margin: 4px;
    color: blue;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<div>
  <button>Feed</button>
  <button>the</button>
  <button>Input</button>
</div>
<input type="text" value="click a button">
​
<script>
$( "button" ).click(function() {
  var text = $( this ).text();
  $( "input" ).val( text );
});
</script>
​
</body>
</html>
```
     * @example ​ ````Use the function argument to modify the value of an input box.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>val demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p>Type something and then click or tab out of the input.</p>
<input type="text" value="type something">
​
<script>
$( "input" ).on( "blur", function() {
  $( this ).val(function( i, val ) {
    return val.toUpperCase();
  });
});
</script>
​
</body>
</html>
```
     * @example ​ ````Set a single select, a multiple select, checkboxes and a radio button .
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>val demo</title>
  <style>
  body {
    color: blue;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<select id="single">
  <option>Single</option>
  <option>Single2</option>
</select>
​
<select id="multiple" multiple="multiple">
  <option selected="selected">Multiple</option>
  <option>Multiple2</option>
  <option selected="selected">Multiple3</option>
</select>
​
<br>
<input type="checkbox" name="checkboxname" value="check1"> check1
<input type="checkbox" name="checkboxname" value="check2"> check2
<input type="radio" name="r" value="radio1"> radio1
<input type="radio" name="r" value="radio2"> radio2
​
<script>
$( "#single" ).val( "Single2" );
$( "#multiple" ).val([ "Multiple2", "Multiple3" ]);
$( "input").val([ "check1", "check2", "radio1" ]);
</script>
​
</body>
</html>
```
     */
    val(value_function: string | number | string[] | ((this: TElement, index: number, value: string) => string)): this;
    /**
     * Get the current value of the first element in the set of matched elements.
     * @see \`{@link https://api.jquery.com/val/ }\`
     * @since 1.0
     * @example ​ ````Get the single value from a single select and an array of values from a multiple select and display their values.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>val demo</title>
  <style>
  p {
    color: red;
    margin: 4px;
  }
  b {
    color: blue;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p></p>
​
<select id="single">
  <option>Single</option>
  <option>Single2</option>
</select>
​
<select id="multiple" multiple="multiple">
  <option selected="selected">Multiple</option>
  <option>Multiple2</option>
  <option selected="selected">Multiple3</option>
</select>
​
<script>
function displayVals() {
  var singleValues = $( "#single" ).val();
  var multipleValues = $( "#multiple" ).val() || [];
  // When using jQuery 3:
  // var multipleValues = $( "#multiple" ).val();
  $( "p" ).html( "<b>Single:</b> " + singleValues +
    " <b>Multiple:</b> " + multipleValues.join( ", " ) );
}
​
$( "select" ).change( displayVals );
displayVals();
</script>
​
</body>
</html>
```
     * @example ​ ````Find the value of an input box.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>val demo</title>
  <style>
  p {
    color: blue;
    margin: 8px;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<input type="text" value="some text">
<p></p>
​
<script>
$( "input" )
  .keyup(function() {
    var value = $( this ).val();
    $( "p" ).text( value );
  })
  .keyup();
</script>
​
</body>
</html>
```
     */
    val(): string | number | string[] | undefined;
    /**
     * Set the CSS width of each element in the set of matched elements.
     * @param value_function _&#x40;param_ `value_function`
     * <br>
     * * `value` — An integer representing the number of pixels, or an integer along with an optional unit of measure
     *             appended (as a string). <br>
     * * `function` — A function returning the width to set. Receives the index position of the element in the set and the
     *                old width as arguments. Within the function, `this` refers to the current element in the set.
     * @see \`{@link https://api.jquery.com/width/ }\`
     * @since 1.0
     * @since 1.4.1
     * @example ​ ````Change the width of each div the first time it is clicked (and change its color).
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>width demo</title>
  <style>
  div {
    width: 70px;
    height: 50px;
    float: left;
    margin: 5px;
    background: red;
    cursor: pointer;
  }
  .mod {
    background: blue;
    cursor: default;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<div>d</div>
<div>d</div>
<div>d</div>
<div>d</div>
<div>d</div>
​
<script>
var modWidth = 50;
$( "div" ).one( "click", function() {
  $( this ).width( modWidth ).addClass( "mod" );
  modWidth -= 8;
});
</script>
​
</body>
</html>
```
     */
    width(value_function: string | number | ((this: TElement, index: number, value: number) => string | number)): this;
    /**
     * Get the current computed width for the first element in the set of matched elements.
     * @see \`{@link https://api.jquery.com/width/ }\`
     * @since 1.0
     * @example ​ ````Show various widths.  Note the values are from the iframe so might be smaller than you expected.  The yellow highlight shows the iframe body.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>width demo</title>
  <style>
  body {
    background: yellow;
  }
  button {
    font-size: 12px;
    margin: 2px;
  }
  p {
    width: 150px;
    border: 1px red solid;
  }
  div {
    color: red;
    font-weight: bold;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<button id="getp">Get Paragraph Width</button>
<button id="getd">Get Document Width</button>
<button id="getw">Get Window Width</button>
<div>&nbsp;</div>
<p>
  Sample paragraph to test width
</p>
​
<script>
function showWidth( ele, w ) {
  $( "div" ).text( "The width for the " + ele + " is " + w + "px." );
}
$( "#getp" ).click(function() {
  showWidth( "paragraph", $( "p" ).width() );
});
$( "#getd" ).click(function() {
  showWidth( "document", $( document ).width() );
});
$("#getw").click(function() {
  showWidth( "window", $( window ).width() );
});
</script>
​
</body>
</html>
```
     */
    width(): number | undefined;
    /**
     * Wrap an HTML structure around each element in the set of matched elements.
     * @param wrappingElement_function _&#x40;param_ `wrappingElement_function`
     * <br>
     * * `wrappingElement` — A selector, element, HTML string, or jQuery object specifying the structure to wrap around the
     *                       matched elements. When you pass a jQuery collection containing more than one element, or a selector
     *                       matching more than one element, the first element will be used. <br>
     * * `function` — A callback function returning the HTML content or jQuery object to wrap around the matched elements.
     *                Receives the index position of the element in the set as an argument. Within the function, `this`
     *                refers to the current element in the set.
     * @see \`{@link https://api.jquery.com/wrap/ }\`
     * @since 1.0
     * @since 1.4
     * @example ​ ````Wrap a new div around all of the paragraphs.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>wrap demo</title>
  <style>
  div {
    border: 2px solid blue;
  }
  p {
    background: yellow;
    margin: 4px;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p>Hello</p>
<p>cruel</p>
<p>World</p>
​
<script>
$( "p" ).wrap( "<div></div>" );
</script>
​
</body>
</html>
```
     * @example ​ ````Wraps a newly created tree of objects around the spans.  Notice anything in between the spans gets left out like the &lt;strong&gt; (red text) in this example.  Even the white space between spans is left out.  Click View Source to see the original html.&gt;
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>wrap demo</title>
  <style>
  div {
    border: 2px blue solid;
    margin: 2px;
    padding: 2px;
  }
  p {
    background: yellow;
    margin: 2px;
    padding: 2px;
  }
  strong {
    color: red;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<span>Span Text</span>
<strong>What about me?</strong>
<span>Another One</span>
​
<script>
$( "span" ).wrap( "<div><div><p><em><b></b></em></p></div></div>" );
</script>
​
</body>
</html>
```
     * @example ​ ````Wrap a new div around all of the paragraphs.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>wrap demo</title>
  <style>
  div {
    border: 2px solid blue;
  }
  p {
    background: yellow;
    margin: 4px;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p>Hello</p>
<p>cruel</p>
<p>World</p>
​
<script>
$( "p" ).wrap( document.createElement( "div" ) );
</script>
​
</body>
</html>
```
     * @example ​ ````Wrap a jQuery object double depth div around all of the paragraphs.  Notice it doesn&#39;t move the object but just clones it to wrap around its target.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>wrap demo</title>
  <style>
  div {
    border: 2px solid blue;
    margin: 2px;
    padding: 2px;
  }
  .doublediv {
    border-color: red;
  }
  p {
    background: yellow;
    margin: 4px;
    font-size: 14px;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p>Hello</p>
<p>cruel</p>
<p>World</p>
<div class="doublediv"><div></div></div>
​
<script>
$( "p" ).wrap( $( ".doublediv" ) );
</script>
​
</body>
</html>
```
     */
    wrap(wrappingElement_function: JQuery.Selector | JQuery.htmlString | Element | JQuery | ((this: TElement, index: number) => string | JQuery)): this;
    /**
     * Wrap an HTML structure around all elements in the set of matched elements.
     * @param wrappingElement_function _&#x40;param_ `wrappingElement_function`
     * <br>
     * * `wrappingElement` — A selector, element, HTML string, or jQuery object specifying the structure to wrap around the matched elements. <br>
     * * `function` — A callback function returning the HTML content or jQuery object to wrap around all the matched
     *                elements. Within the function, `this` refers to the first element in the set. **Prior to jQuery
     *                3.0**, the callback was incorrectly called for every element in the set and received the index
     *                position of the element in the set as an argument.
     * @see \`{@link https://api.jquery.com/wrapAll/ }\`
     * @since 1.2
     * @since 1.4
     * @example ​ ````Wrap a new div around all of the paragraphs.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>wrapAll demo</title>
  <style>
  div {
    border: 2px solid blue;
  }
  p {
    background: yellow;
    margin: 4px;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p>Hello</p>
<p>cruel</p>
<p>World</p>
​
<script>
$( "p" ).wrapAll( "<div></div>" );
</script>
​
</body>
</html>
```
     * @example ​ ````Wraps a newly created tree of objects around the spans.  Notice anything in between the spans gets left out like the &lt;strong&gt; (red text) in this example.  Even the white space between spans is left out.  Click View Source to see the original html.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>wrapAll demo</title>
  <style>
  div {
    border: 2px blue solid;
    margin: 2px;
    padding: 2px;
  }
  p {
    background: yellow;
    margin: 2px;
    padding: 2px;
  }
  strong {
    color: red;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<span>Span Text</span>
<strong>What about me?</strong>
<span>Another One</span>
​
<script>
$( "span").wrapAll( "<div><div><p><em><b></b></em></p></div></div>" );
</script>
​
</body>
</html>
```
     * @example ​ ````Wrap a new div around all of the paragraphs.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>wrapAll demo</title>
  <style>
  div {
    border: 2px solid blue;
  }
  p {
    background: yellow;
    margin: 4px;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p>Hello</p>
<p>cruel</p>
<p>World</p>
​
<script>
$( "p" ).wrapAll( document.createElement( "div" ) );
</script>
​
</body>
</html>
```
     * @example ​ ````Wrap a jQuery object double depth div around all of the paragraphs.  Notice it doesn&#39;t move the object but just clones it to wrap around its target.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>wrapAll demo</title>
  <style>
  div {
    border: 2px solid blue;
    margin: 2px;
    padding: 2px;
  }
  .doublediv {
    border-color: red;
  }
  p {
    background: yellow;
    margin: 4px;
    font-size: 14px;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p>Hello</p>
<p>cruel</p>
<p>World</p>
<div class="doublediv"><div></div></div>
​
<script>
$( "p" ).wrapAll( $( ".doublediv" ) );
</script>
​
</body>
</html>
```
     */
    wrapAll(wrappingElement_function: JQuery.Selector | JQuery.htmlString | Element | JQuery | ((this: TElement) => string | JQuery)): this;
    /**
     * Wrap an HTML structure around the content of each element in the set of matched elements.
     * @param wrappingElement_function _&#x40;param_ `wrappingElement_function`
     * <br>
     * * `wrappingElement` — An HTML snippet, selector expression, jQuery object, or DOM element specifying the structure to wrap
     *                       around the content of the matched elements. <br>
     * * `function` — A callback function which generates a structure to wrap around the content of the matched elements.
     *                Receives the index position of the element in the set as an argument. Within the function, `this`
     *                refers to the current element in the set.
     * @see \`{@link https://api.jquery.com/wrapInner/ }\`
     * @since 1.2
     * @since 1.4
     * @example ​ ````Selects all paragraphs and wraps a bold tag around each of its contents.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>wrapInner demo</title>
  <style>
  p {
    background: #bbf;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p>Hello</p>
<p>cruel</p>
<p>World</p>
​
<script>
$( "p" ).wrapInner( "<b></b>" );
</script>
​
</body>
</html>
```
     * @example ​ ````Wraps a newly created tree of objects around the inside of the body.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>wrapInner demo</title>
  <style>
  div {
    border: 2px green solid;
    margin: 2px;
    padding: 2px;
  }
  p {
    background: yellow;
    margin: 2px;
    padding: 2px;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
Plain old text, or is it?
​
<script>
$( "body" ).wrapInner( "<div><div><p><em><b></b></em></p></div></div>" );
</script>
​
</body>
</html>
```
     * @example ​ ````Selects all paragraphs and wraps a bold tag around each of its contents.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>wrapInner demo</title>
  <style>
  p {
    background: #9f9;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p>Hello</p>
<p>cruel</p>
<p>World</p>
​
<script>
$( "p" ).wrapInner( document.createElement( "b" ) );
</script>
​
</body>
</html>
```
     * @example ​ ````Selects all paragraphs and wraps a jQuery object around each of its contents.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>wrapInner demo</title>
  <style>
  p {
    background: #9f9;
  }
  .red {
    color: red;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p>Hello</p>
<p>cruel</p>
<p>World</p>
​
<script>
$( "p" ).wrapInner( $( "<span class='red'></span>" ) );
</script>
​
</body>
</html>
```
     */
    wrapInner(wrappingElement_function: JQuery.Selector | JQuery.htmlString | Element | JQuery | ((this: TElement, index: number) => string | JQuery | Element)): this;

    [n: number]: TElement;
}
