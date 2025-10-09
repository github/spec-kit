'use strict';

Object.defineProperty(exports, '__esModule', { value: true });

// TODO: including these in blob-util.ts causes typedoc to generate docs for them,
// even with --excludePrivate ¯\_(ツ)_/¯
/** @private */
function loadImage(src, crossOrigin) {
    return new Promise(function (resolve, reject) {
        var img = new Image();
        if (crossOrigin) {
            img.crossOrigin = crossOrigin;
        }
        img.onload = function () {
            resolve(img);
        };
        img.onerror = reject;
        img.src = src;
    });
}
/** @private */
function imgToCanvas(img) {
    var canvas = document.createElement('canvas');
    canvas.width = img.width;
    canvas.height = img.height;
    // copy the image contents to the canvas
    var context = canvas.getContext('2d');
    context.drawImage(img, 0, 0, img.width, img.height, 0, 0, img.width, img.height);
    return canvas;
}

/* global Promise, Image, Blob, FileReader, atob, btoa,
   BlobBuilder, MSBlobBuilder, MozBlobBuilder, WebKitBlobBuilder, webkitURL */
/**
 * Shim for
 * [`new Blob()`](https://developer.mozilla.org/en-US/docs/Web/API/Blob.Blob)
 * to support
 * [older browsers that use the deprecated `BlobBuilder` API](http://caniuse.com/blob).
 *
 * Example:
 *
 * ```js
 * var myBlob = blobUtil.createBlob(['hello world'], {type: 'text/plain'});
 * ```
 *
 * @param parts - content of the Blob
 * @param properties - usually `{type: myContentType}`,
 *                           you can also pass a string for the content type
 * @returns Blob
 */
function createBlob(parts, properties) {
    parts = parts || [];
    properties = properties || {};
    if (typeof properties === 'string') {
        properties = { type: properties }; // infer content type
    }
    try {
        return new Blob(parts, properties);
    }
    catch (e) {
        if (e.name !== 'TypeError') {
            throw e;
        }
        var Builder = typeof BlobBuilder !== 'undefined'
            ? BlobBuilder : typeof MSBlobBuilder !== 'undefined'
            ? MSBlobBuilder : typeof MozBlobBuilder !== 'undefined'
            ? MozBlobBuilder : WebKitBlobBuilder;
        var builder = new Builder();
        for (var i = 0; i < parts.length; i += 1) {
            builder.append(parts[i]);
        }
        return builder.getBlob(properties.type);
    }
}
/**
 * Shim for
 * [`URL.createObjectURL()`](https://developer.mozilla.org/en-US/docs/Web/API/URL.createObjectURL)
 * to support browsers that only have the prefixed
 * `webkitURL` (e.g. Android <4.4).
 *
 * Example:
 *
 * ```js
 * var myUrl = blobUtil.createObjectURL(blob);
 * ```
 *
 * @param blob
 * @returns url
 */
function createObjectURL(blob) {
    return (typeof URL !== 'undefined' ? URL : webkitURL).createObjectURL(blob);
}
/**
 * Shim for
 * [`URL.revokeObjectURL()`](https://developer.mozilla.org/en-US/docs/Web/API/URL.revokeObjectURL)
 * to support browsers that only have the prefixed
 * `webkitURL` (e.g. Android <4.4).
 *
 * Example:
 *
 * ```js
 * blobUtil.revokeObjectURL(myUrl);
 * ```
 *
 * @param url
 */
function revokeObjectURL(url) {
    return (typeof URL !== 'undefined' ? URL : webkitURL).revokeObjectURL(url);
}
/**
 * Convert a `Blob` to a binary string.
 *
 * Example:
 *
 * ```js
 * blobUtil.blobToBinaryString(blob).then(function (binaryString) {
 *   // success
 * }).catch(function (err) {
 *   // error
 * });
 * ```
 *
 * @param blob
 * @returns Promise that resolves with the binary string
 */
function blobToBinaryString(blob) {
    return new Promise(function (resolve, reject) {
        var reader = new FileReader();
        var hasBinaryString = typeof reader.readAsBinaryString === 'function';
        reader.onloadend = function () {
            var result = reader.result || '';
            if (hasBinaryString) {
                return resolve(result);
            }
            resolve(arrayBufferToBinaryString(result));
        };
        reader.onerror = reject;
        if (hasBinaryString) {
            reader.readAsBinaryString(blob);
        }
        else {
            reader.readAsArrayBuffer(blob);
        }
    });
}
/**
 * Convert a base64-encoded string to a `Blob`.
 *
 * Example:
 *
 * ```js
 * var blob = blobUtil.base64StringToBlob(base64String);
 * ```
 * @param base64 - base64-encoded string
 * @param type - the content type (optional)
 * @returns Blob
 */
function base64StringToBlob(base64, type) {
    var parts = [binaryStringToArrayBuffer(atob(base64))];
    return type ? createBlob(parts, { type: type }) : createBlob(parts);
}
/**
 * Convert a binary string to a `Blob`.
 *
 * Example:
 *
 * ```js
 * var blob = blobUtil.binaryStringToBlob(binaryString);
 * ```
 *
 * @param binary - binary string
 * @param type - the content type (optional)
 * @returns Blob
 */
function binaryStringToBlob(binary, type) {
    return base64StringToBlob(btoa(binary), type);
}
/**
 * Convert a `Blob` to a binary string.
 *
 * Example:
 *
 * ```js
 * blobUtil.blobToBase64String(blob).then(function (base64String) {
 *   // success
 * }).catch(function (err) {
 *   // error
 * });
 * ```
 *
 * @param blob
 * @returns Promise that resolves with the binary string
 */
function blobToBase64String(blob) {
    return blobToBinaryString(blob).then(btoa);
}
/**
 * Convert a data URL string
 * (e.g. `'data:image/png;base64,iVBORw0KG...'`)
 * to a `Blob`.
 *
 * Example:
 *
 * ```js
 * var blob = blobUtil.dataURLToBlob(dataURL);
 * ```
 *
 * @param dataURL - dataURL-encoded string
 * @returns Blob
 */
function dataURLToBlob(dataURL) {
    var type = dataURL.match(/data:([^;]+)/)[1];
    var base64 = dataURL.replace(/^[^,]+,/, '');
    var buff = binaryStringToArrayBuffer(atob(base64));
    return createBlob([buff], { type: type });
}
/**
 * Convert a `Blob` to a data URL string
 * (e.g. `'data:image/png;base64,iVBORw0KG...'`).
 *
 * Example:
 *
 * ```js
 * var dataURL = blobUtil.blobToDataURL(blob);
 * ```
 *
 * @param blob
 * @returns Promise that resolves with the data URL string
 */
function blobToDataURL(blob) {
    return blobToBase64String(blob).then(function (base64String) {
        return 'data:' + blob.type + ';base64,' + base64String;
    });
}
/**
 * Convert an image's `src` URL to a data URL by loading the image and painting
 * it to a `canvas`.
 *
 * Note: this will coerce the image to the desired content type, and it
 * will only paint the first frame of an animated GIF.
 *
 * Examples:
 *
 * ```js
 * blobUtil.imgSrcToDataURL('http://mysite.com/img.png').then(function (dataURL) {
 *   // success
 * }).catch(function (err) {
 *   // error
 * });
 * ```
 *
 * ```js
 * blobUtil.imgSrcToDataURL('http://some-other-site.com/img.jpg', 'image/jpeg',
 *                          'Anonymous', 1.0).then(function (dataURL) {
 *   // success
 * }).catch(function (err) {
 *   // error
 * });
 * ```
 *
 * @param src - image src
 * @param type - the content type (optional, defaults to 'image/png')
 * @param crossOrigin - for CORS-enabled images, set this to
 *                                         'Anonymous' to avoid "tainted canvas" errors
 * @param quality - a number between 0 and 1 indicating image quality
 *                                     if the requested type is 'image/jpeg' or 'image/webp'
 * @returns Promise that resolves with the data URL string
 */
function imgSrcToDataURL(src, type, crossOrigin, quality) {
    type = type || 'image/png';
    return loadImage(src, crossOrigin).then(imgToCanvas).then(function (canvas) {
        return canvas.toDataURL(type, quality);
    });
}
/**
 * Convert a `canvas` to a `Blob`.
 *
 * Examples:
 *
 * ```js
 * blobUtil.canvasToBlob(canvas).then(function (blob) {
 *   // success
 * }).catch(function (err) {
 *   // error
 * });
 * ```
 *
 * Most browsers support converting a canvas to both `'image/png'` and `'image/jpeg'`. You may
 * also want to try `'image/webp'`, which will work in some browsers like Chrome (and in other browsers, will just fall back to `'image/png'`):
 *
 * ```js
 * blobUtil.canvasToBlob(canvas, 'image/webp').then(function (blob) {
 *   // success
 * }).catch(function (err) {
 *   // error
 * });
 * ```
 *
 * @param canvas - HTMLCanvasElement
 * @param type - the content type (optional, defaults to 'image/png')
 * @param quality - a number between 0 and 1 indicating image quality
 *                                     if the requested type is 'image/jpeg' or 'image/webp'
 * @returns Promise that resolves with the `Blob`
 */
function canvasToBlob(canvas, type, quality) {
    if (typeof canvas.toBlob === 'function') {
        return new Promise(function (resolve) {
            canvas.toBlob(resolve, type, quality);
        });
    }
    return Promise.resolve(dataURLToBlob(canvas.toDataURL(type, quality)));
}
/**
 * Convert an image's `src` URL to a `Blob` by loading the image and painting
 * it to a `canvas`.
 *
 * Note: this will coerce the image to the desired content type, and it
 * will only paint the first frame of an animated GIF.
 *
 * Examples:
 *
 * ```js
 * blobUtil.imgSrcToBlob('http://mysite.com/img.png').then(function (blob) {
 *   // success
 * }).catch(function (err) {
 *   // error
 * });
 * ```
 *
 * ```js
 * blobUtil.imgSrcToBlob('http://some-other-site.com/img.jpg', 'image/jpeg',
 *                          'Anonymous', 1.0).then(function (blob) {
 *   // success
 * }).catch(function (err) {
 *   // error
 * });
 * ```
 *
 * @param src - image src
 * @param type - the content type (optional, defaults to 'image/png')
 * @param crossOrigin - for CORS-enabled images, set this to
 *                                         'Anonymous' to avoid "tainted canvas" errors
 * @param quality - a number between 0 and 1 indicating image quality
 *                                     if the requested type is 'image/jpeg' or 'image/webp'
 * @returns Promise that resolves with the `Blob`
 */
function imgSrcToBlob(src, type, crossOrigin, quality) {
    type = type || 'image/png';
    return loadImage(src, crossOrigin).then(imgToCanvas).then(function (canvas) {
        return canvasToBlob(canvas, type, quality);
    });
}
/**
 * Convert an `ArrayBuffer` to a `Blob`.
 *
 * Example:
 *
 * ```js
 * var blob = blobUtil.arrayBufferToBlob(arrayBuff, 'audio/mpeg');
 * ```
 *
 * @param buffer
 * @param type - the content type (optional)
 * @returns Blob
 */
function arrayBufferToBlob(buffer, type) {
    return createBlob([buffer], type);
}
/**
 * Convert a `Blob` to an `ArrayBuffer`.
 *
 * Example:
 *
 * ```js
 * blobUtil.blobToArrayBuffer(blob).then(function (arrayBuff) {
 *   // success
 * }).catch(function (err) {
 *   // error
 * });
 * ```
 *
 * @param blob
 * @returns Promise that resolves with the `ArrayBuffer`
 */
function blobToArrayBuffer(blob) {
    return new Promise(function (resolve, reject) {
        var reader = new FileReader();
        reader.onloadend = function () {
            var result = reader.result || new ArrayBuffer(0);
            resolve(result);
        };
        reader.onerror = reject;
        reader.readAsArrayBuffer(blob);
    });
}
/**
 * Convert an `ArrayBuffer` to a binary string.
 *
 * Example:
 *
 * ```js
 * var myString = blobUtil.arrayBufferToBinaryString(arrayBuff)
 * ```
 *
 * @param buffer - array buffer
 * @returns binary string
 */
function arrayBufferToBinaryString(buffer) {
    var binary = '';
    var bytes = new Uint8Array(buffer);
    var length = bytes.byteLength;
    var i = -1;
    while (++i < length) {
        binary += String.fromCharCode(bytes[i]);
    }
    return binary;
}
/**
 * Convert a binary string to an `ArrayBuffer`.
 *
 * ```js
 * var myBuffer = blobUtil.binaryStringToArrayBuffer(binaryString)
 * ```
 *
 * @param binary - binary string
 * @returns array buffer
 */
function binaryStringToArrayBuffer(binary) {
    var length = binary.length;
    var buf = new ArrayBuffer(length);
    var arr = new Uint8Array(buf);
    var i = -1;
    while (++i < length) {
        arr[i] = binary.charCodeAt(i);
    }
    return buf;
}

exports.createBlob = createBlob;
exports.createObjectURL = createObjectURL;
exports.revokeObjectURL = revokeObjectURL;
exports.blobToBinaryString = blobToBinaryString;
exports.base64StringToBlob = base64StringToBlob;
exports.binaryStringToBlob = binaryStringToBlob;
exports.blobToBase64String = blobToBase64String;
exports.dataURLToBlob = dataURLToBlob;
exports.blobToDataURL = blobToDataURL;
exports.imgSrcToDataURL = imgSrcToDataURL;
exports.canvasToBlob = canvasToBlob;
exports.imgSrcToBlob = imgSrcToBlob;
exports.arrayBufferToBlob = arrayBufferToBlob;
exports.blobToArrayBuffer = blobToArrayBuffer;
exports.arrayBufferToBinaryString = arrayBufferToBinaryString;
exports.binaryStringToArrayBuffer = binaryStringToArrayBuffer;
