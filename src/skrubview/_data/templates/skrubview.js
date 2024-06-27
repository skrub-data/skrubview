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
    const bar = reportElem.querySelector(".selected-columns-box");
    bar.textContent = "[" + snippet + "]";
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
    reportElem.querySelectorAll(".skrubview-column-summary").forEach(
        elem => {
            const box = elem.querySelector("input.skrubview-select-column-checkbox[type='checkbox']");
            if (!(box === null)) {
                box.checked = !elem.hasAttribute("data-is-excluded-by-filter");
            }
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

    const topBarId = table.dataset.topBarId;
    const bar = document.getElementById(topBarId);
    bar.setAttribute(`data-content-table-cell-value`, elem.dataset.valueStr);
    bar.setAttribute(`data-content-table-cell-repr`, elem.dataset.valueRepr);
    bar.setAttribute(`data-content-table-column-name`, elem.dataset.colNameStr);
    bar.setAttribute(`data-content-table-column-name-repr`, elem.dataset.colNameRepr);

    const snippet = filterSnippet(elem.dataset.columnNameRepr,
        elem.dataset.valueRepr,
        elem.hasAttribute("data-value-is-none"),
        elem.dataset.dataframeModule);
    bar.setAttribute(`data-content-table-cell-filter`, snippet);

    revealColCard(table.dataset.reportId, elem.dataset.columnIdx);

    updateBarContent(topBarId);
}

function revealColCard(reportId, colIdx) {
    const reportElem = document.getElementById(reportId);
    const allCols = reportElem.querySelectorAll(".skrubview-columns-in-sample-tab .skrubview-column-summary");
    allCols.forEach(col => {
        col.removeAttribute("data-is-selected-in-table");
    });
    const targetCol = document.getElementById(`${reportId}_col_${colIdx}_in_sample_tab`);
    targetCol.dataset.isSelectedInTable = "";

}

function displayTab(event) {
    const elem = event.target;
    elem.parentElement.querySelectorAll("button").forEach(elem => {
        elem.removeAttribute("data-is-selected");
    });
    elem.setAttribute("data-is-selected", "");
    const tab = document.getElementById(elem.dataset.targetTab);
    tab.parentElement.querySelectorAll(".skrubview-tab").forEach(elem => {
        elem.removeAttribute("data-is-displayed");
    });
    tab.setAttribute("data-is-displayed", "");
    if (elem.hasAttribute("data-has-warning")){
        elem.removeAttribute("data-has-warning");
    }
}

function onFilterChange(colFilterId) {
    const selectElem = document.getElementById(colFilterId);
    const reportId = selectElem.dataset.reportId;
    const colFilters = window[`columnFiltersForReport${reportId}`];
    const acceptedCols = colFilters[selectElem.value];
    const reportElem = document.getElementById(reportId);
    const colElements = reportElem.querySelectorAll(".skrubview-filterable-column");
    colElements.forEach(elem => {
        if (acceptedCols.includes(elem.dataset.columnName)) {
            elem.removeAttribute("data-is-excluded-by-filter");
        } else {
            elem.dataset.isExcludedByFilter = "";
        }
    })
    document.getElementById(`${reportId}_display_n_columns`).textContent = acceptedCols.length.toString();
}
