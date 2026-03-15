/**
 * Generates a table of contents from h1-h6 headings and inserts it into the first <nav> element.
 * Configure heading levels via data-toc-start and data-toc-end attributes (e.g., <nav data-toc-start="2" data-toc-end="4">).
 * Add class="toc-ignore" to any heading to exclude it and all its sub-sections from the TOC.
 */
function createToc(content) {
    const tocContainer = content.querySelector('nav');
    if (!tocContainer) {
        console.debug("No <nav> element found for TOC");
        return;
    }

    const startLevel = parseInt(tocContainer.dataset.tocStart) || 1;
    const endLevel = parseInt(tocContainer.dataset.tocEnd) || 6;

    const tocList = document.createElement('ul');
    tocList.id = 'list-toc-generated';
    tocContainer.innerHTML = '';
    tocContainer.appendChild(tocList);

    let idCounter = 0;

    // Collect ALL headings (needed for ignore logic and counter matching)
    const headings = [...content.querySelectorAll('h1, h2, h3, h4, h5, h6')].map(el => ({
        element: el,
        level: parseInt(el.tagName[1])
    }));

    // Pass 1: Mark ALL elements with hierarchical ignore logic
    let ignoreUntilLevel = null;
    headings.forEach(({ element, level }) => {
        if (ignoreUntilLevel !== null && level <= ignoreUntilLevel) {
            ignoreUntilLevel = null;
        }

        // Mark headings outside the configured range as ignored
        if (level < startLevel || level > endLevel) {
            element.classList.add('toc-ignored');
            return;
        }

        if (element.classList.contains('toc-ignore')) {
            ignoreUntilLevel = level;
            element.classList.add('toc-ignored');
            return;
        }

        if (ignoreUntilLevel !== null && level > ignoreUntilLevel) {
            element.classList.add('toc-ignored');
            return;
        }

        element.classList.add('title-element');
        if (!element.id) {
            element.id = `title-element-${++idCounter}`;
        }
    });

    // Pass 2: Number headings and build TOC with JavaScript counters
    const counters = [0, 0, 0, 0, 0, 0];
    const listStack = [{ list: tocList, level: startLevel - 1 }];

    content.querySelectorAll('.title-element').forEach(element => {
        const level = parseInt(element.tagName[1]);
        if (level >= startLevel && level <= endLevel) {
            const idx = level - startLevel;
            counters[idx]++;
            counters.fill(0, idx + 1);

            const number = counters.slice(0, idx + 1).join('.') + ' ';

            // Add number to heading
            element.textContent = number + element.textContent;

            // Navigate to correct nesting level
            while (listStack.length > 1 && listStack[listStack.length - 1].level >= level) {
                listStack.pop();
            }

            // Create new list item
            const li = document.createElement('li');
            li.className = `toc-element toc-element-level-${level}`;
            li.innerHTML = `<a href="#${element.id}">${element.textContent}</a>`;
            listStack[listStack.length - 1].list.appendChild(li);

            // Prepare for potential nested list
            const nestedList = document.createElement('ul');
            li.appendChild(nestedList);
            listStack.push({ list: nestedList, level });
        }
    });
}
