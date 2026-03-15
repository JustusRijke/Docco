class LandscapeHandler extends Paged.Handler {
    afterRendered(pages) {
        for (const page of pages) {
            if (page.element.classList.contains('pagedjs_landscape_page'))
                page.element.classList.add("landscape_page");
        }
    }
}
Paged.registerHandlers(LandscapeHandler);
