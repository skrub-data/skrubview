function highlightColCard(reportId, colIdx){
    const reportElem = document.getElementById(reportId);
    const allCols = reportElem.querySelectorAll(".skrubview-column-summary");
    allCols.forEach(col => {col.removeAttribute("data-is-highlighted");});
    const targetCol = document.getElementById(`${reportId}_col_${colIdx}`);
    targetCol.dataset.isHighlighted = "";
}


function updateColSelection(event) {
    updateSelectedColsSnippet(event.target.dataset.reportId);
}

function isSelectedCol(columnElem) {
    const checkboxElem = columnElem.querySelector("input.skrubview-select-column-checkbox[type='checkbox']");
    return checkboxElem && checkboxElem.checked;
}

function updateSelectedColsSnippet(reportId, updateBarMode=true) {
    const reportElem = document.getElementById(reportId);
    const allCols = reportElem.querySelectorAll(".skrubview-column-summary");
    const selectedCols = Array.from(allCols).filter(c => isSelectedCol(c));
    const snippet = selectedCols.map(col => col.dataset.nameRepr).join(", ");
    const bar = reportElem.querySelector(".skrubview-powerbar > .skrubview-box");
    bar.setAttribute("data-content-selected-columns", "[" + snippet + "]");
    if(updateBarMode){
        selectOneOf(bar.id, ["selected-columns"]);
    }
    updateBarContent(bar.id);
}

function clearSelectedCols(reportId) {
    const reportElem = document.getElementById(reportId);
    reportElem.querySelectorAll("input.skrubview-select-column-checkbox[type='checkbox']").forEach(
        box => {
            box.checked = false;
        }
    );
    updateSelectedColsSnippet(reportId);
}

function selectAllCols(reportId) {
    const reportElem = document.getElementById(reportId);
    reportElem.querySelectorAll("input.skrubview-select-column-checkbox[type='checkbox']").forEach(
        box => {
            box.checked = true;
        }
    );
    updateSelectedColsSnippet(reportId);
}


function copyTextToClipboard(elementID) {
    const elem = document.getElementById(elementID);
    if (elem.hasAttribute("data-shows-placeholder")) {
        return;
    }
    elem.setAttribute("data-is-being-copied", "");
    if (navigator.clipboard) {
        navigator.clipboard.writeText(elem.textContent || "");
    } else {
        const selection = window.getSelection();
        if (selection == null) {
            return;
        }
        selection.removeAllRanges();
        const range = document.createRange();
        range.selectNodeContents(elem);
        selection.addRange(range);
        document.execCommand("copy");
        selection.removeAllRanges();
    }

    setTimeout(() => {
        elem.removeAttribute("data-is-being-copied");
    }, 200);
}

function pandasFilterSnippet(colName, value, valueIsNone) {
    if (valueIsNone) {
        return `df.loc[df[${colName}].isnull()]`;
    }
    return `df.loc[df[${colName}] == ${value}]`;
}

function polarsFilterSnippet(colName, value, valueIsNone) {
    if (valueIsNone) {
        return `df.filter(pl.col(${colName}).is_null())`;
    }
    return `df.filter(pl.col(${colName}) == ${value})`;
}

function filterSnippet(colName, value, valueIsNone, dataframeModule) {
    if (dataframeModule === "polars") {
        return polarsFilterSnippet(colName, value, valueIsNone);
    }
    if (dataframeModule === "pandas") {
        return pandasFilterSnippet(colName, value, valueIsNone);
    }
    return `Unknown dataframe library: ${dataframeModule}`;
}

function selectOneOf(barId, options) {
    const bar = document.getElementById(barId);
    const select = document.getElementById(bar.dataset.selectorId);
    const selectedOptionValue = select.value;
    if (options.includes(selectedOptionValue)) {
        return;
    }
    select.value = options[0];
}

function updateBarContent(barId) {
    const bar = document.getElementById(barId);
    const select = document.getElementById(bar.dataset.selectorId);
    const selectedOption = select.options[select.selectedIndex];
    const selectedOptionValue = selectedOption.value;
    const contentAttribute = `data-content-${selectedOptionValue}`;
    if (!bar.hasAttribute(contentAttribute)) {
        bar.textContent = selectedOption.dataset.placeholder;
        bar.dataset.showsPlaceholder = "";
    } else {
        bar.textContent = bar.getAttribute(contentAttribute);
        bar.removeAttribute("data-shows-placeholder");
    }
}

function updateSiblingBarContents(event) {
    const select = event.target;
    select.parentElement.querySelectorAll(`*[data-selector-id=${select.id}]`).forEach(
        elem => {
            updateBarContent(elem.id);
        })
}


function displayValue(event) {
    const elem = event.target;
    const table = document.getElementById(elem.dataset.parentTableId);
    table.querySelectorAll(".skrubview-table-cell").forEach(cell => {
        cell.removeAttribute("data-is-selected");
    });
    elem.setAttribute("data-is-selected", "");

    const powerbarId = table.dataset.powerbarId;
    const bar = document.getElementById(powerbarId);
    bar.setAttribute(`data-content-table-cell-value`, elem.dataset.valueStr);
    bar.setAttribute(`data-content-table-cell-repr`, elem.dataset.valueRepr);

    const snippet = filterSnippet(elem.dataset.columnNameRepr,
        elem.dataset.valueRepr,
        elem.hasAttribute("data-value-is-none"),
        elem.dataset.dataframeModule);
    bar.setAttribute(`data-content-table-cell-filter`, snippet);

    selectOneOf(powerbarId, ["table-cell-value", "table-cell-repr", "table-cell-filter"]);
    updateBarContent(powerbarId);

    highlightColCard(table.dataset.reportId, elem.dataset.columnIdx);
}
