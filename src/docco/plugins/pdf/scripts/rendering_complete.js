if (typeof Paged !== "undefined") {
    class _ReadyHandler extends Paged.Handler {
        afterRendered() { window.pagedJsRenderingComplete = true; }
    }
    Paged.registerHandlers(_ReadyHandler);
} else {
    window.pagedJsRenderingComplete = true;
}
