class TocHandler extends Paged.Handler {
    beforeParsed(content) {
        createToc(content);
    }
}
Paged.registerHandlers(TocHandler);
