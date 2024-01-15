function updateColSelection(event) {
    updateSelectedColsSnippet(event.target.dataset.reportId);
}

function isSelectedCol(columnElem) {
    const checkboxElem = columnElem.querySelector("input.skrubview-select-column-checkbox[type='checkbox']");
    return checkboxElem && checkboxElem.checked;
}

function updateSelectedColsSnippet(reportId) {
    const reportElem = document.getElementById(reportId);
    const allCols = reportElem.querySelectorAll(".skrubview-column-summary");
    const selectedCols = Array.from(allCols).filter(c => isSelectedCol(c));
    const snippet = selectedCols.map(col => col.dataset.nameRepr).join(", ");
    const selectedColsElem = reportElem.querySelector(".skrubview-selected-columns");
    selectedColsElem.textContent = "[" + snippet + "]";
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
    if (valueIsNone){
        return `df.loc[df[${colName}].isnull()]`;
    }
    return `df.loc[df[${colName}] == ${value}]`;
}

function polarsFilterSnippet(colName, value, valueIsNone) {
    if (valueIsNone){
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

function updateSelectedSnippet(event){
    const elem = event.target;
    let sibling = elem.nextElementSibling;
    while (sibling){
        if(sibling.dataset.optionValue === elem.value) {
            sibling.setAttribute("data-is-selected", "");
        }
        else {
            sibling.removeAttribute("data-is-selected", "");
        }
        sibling = sibling.nextElementSibling;
    }

}

function displayValue(event) {
    const elem = event.target;
    const table = document.getElementById(elem.dataset.parentTableId);
    table.querySelectorAll(".skrubview-table-cell").forEach(cell => {
        cell.removeAttribute("data-is-selected");
    });
    elem.setAttribute("data-is-selected", "");

    const displayBoxId = elem.dataset.displayBoxId;
    const displayBox = document.getElementById(displayBoxId);
    displayBox.removeAttribute("data-shows-placeholder");
    if (displayBox.hasAttribute("data-copybutton-id")) {
        document.getElementById(displayBox.dataset.copybuttonId).removeAttribute("disabled");
    }
    displayBox.textContent = elem.dataset.valueStr;


    const reprBoxId = elem.dataset.valueReprBoxId;
    const reprBox = document.getElementById(reprBoxId);
    reprBox.removeAttribute("data-shows-placeholder");
    if (reprBox.hasAttribute("data-copybutton-id")) {
        document.getElementById(reprBox.dataset.copybuttonId).removeAttribute("disabled");
    }
    reprBox.textContent = elem.dataset.valueRepr;


    const snippetBoxId = elem.dataset.filterSnippetBoxId;
    const snippetBox = document.getElementById(snippetBoxId);
    snippetBox.removeAttribute("data-shows-placeholder");
    if (snippetBox.hasAttribute("data-copybutton-id")) {
        document.getElementById(snippetBox.dataset.copybuttonId).removeAttribute("disabled");
    }
    snippetBox.textContent = filterSnippet(elem.dataset.columnNameRepr,
                                           elem.dataset.valueRepr,
                                           elem.hasAttribute("data-value-is-none"),
                                           elem.dataset.dataframeModule);
}
