"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.getRenderer = void 0;
const default_renderer_1 = require("../renderer/default.renderer");
const silent_renderer_1 = require("../renderer/silent.renderer");
const simple_renderer_1 = require("../renderer/simple.renderer");
const verbose_renderer_1 = require("../renderer/verbose.renderer");
const assert_1 = require("./assert");
const renderers = {
    default: default_renderer_1.DefaultRenderer,
    simple: simple_renderer_1.SimpleRenderer,
    verbose: verbose_renderer_1.VerboseRenderer,
    silent: silent_renderer_1.SilentRenderer
};
function isRendererSupported(renderer) {
    return process.stdout.isTTY === true || renderer.nonTTY === true;
}
function getRendererClass(renderer) {
    if (typeof renderer === 'string') {
        return renderers[renderer] || renderers.default;
    }
    return typeof renderer === 'function' ? renderer : renderers.default;
}
function getRenderer(renderer, fallbackRenderer, fallbackCondition, silentCondition) {
    let returnValue;
    let ret = getRendererClass(renderer);
    returnValue = { renderer: ret, nonTTY: false };
    const evaluateSilent = (0, assert_1.assertFunctionOrSelf)(silentCondition);
    const evaluateFallback = (0, assert_1.assertFunctionOrSelf)(fallbackCondition);
    if (evaluateSilent) {
        ret = getRendererClass('silent');
        returnValue = { renderer: ret, nonTTY: true };
    }
    else if (!isRendererSupported(ret) || evaluateFallback) {
        ret = getRendererClass(fallbackRenderer);
        returnValue = { renderer: ret, nonTTY: true };
    }
    return returnValue;
}
exports.getRenderer = getRenderer;
