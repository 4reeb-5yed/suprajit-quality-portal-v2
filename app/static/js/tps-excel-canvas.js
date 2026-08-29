/**
 * Pure In-Browser Custom OpenXML Canvas Spreadsheet & Chart Engine
 * Built specifically for Suprajit LabVIEW TPS Quality Inspection Reports
 * 100% Client-Side • Zero Dependencies • Zero Watermarks • Zero Server Load
 */

class TpsExcelEngine {
    constructor(canvasContainer, options = {}) {
        this.container = canvasContainer;
        this.options = options;
        this.activeSheetName = 'REPORT';
        this.workbook = null;
        this.sharedStrings = [];
        this.styles = { fills: [], fonts: [], borders: [], cellXfs: [] };
        this.sheetData = {};
        this.charts = {};
        this.scrollX = 0;
        this.scrollY = 0;
        this.zoom = 1.0;
        this.defaultRowHeight = 22;
        this.defaultColWidth = 85;
        this.headerColWidth = 40;
        this.headerRowHeight = 24;
        
        this.initCanvas();
        this.initEventListeners();
    }

    initCanvas() {
        this.container.innerHTML = '';
        this.container.style.position = 'relative';
        this.container.style.overflow = 'hidden';
        this.container.style.width = '100%';
        this.container.style.height = '100%';
        this.container.style.backgroundColor = '#f1f5f9';

        this.canvas = document.createElement('canvas');
        this.canvas.style.display = 'block';
        this.canvas.style.width = '100%';
        this.canvas.style.height = '100%';
        this.container.appendChild(this.canvas);
        this.ctx = this.canvas.getContext('2d', { alpha: false });

        this.resize();
    }

    resize() {
        const rect = this.container.getBoundingClientRect();
        const dpr = window.devicePixelRatio || 1;
        this.width = rect.width;
        this.height = rect.height;

        this.canvas.width = this.width * dpr;
        this.canvas.height = this.height * dpr;
        this.ctx.scale(dpr, dpr);

        this.render();
    }

    initEventListeners() {
        window.addEventListener('resize', () => this.resize());

        this.canvas.addEventListener('wheel', (e) => {
            e.preventDefault();
            if (e.ctrlKey) {
                const zoomFactor = e.deltaY < 0 ? 1.1 : 0.9;
                this.zoom = Math.min(Math.max(0.5, this.zoom * zoomFactor), 2.0);
            } else {
                this.scrollX = Math.max(0, this.scrollX + e.deltaX);
                this.scrollY = Math.max(0, this.scrollY + e.deltaY);
            }
            this.render();
        }, { passive: false });

        let isDragging = false;
        let startX, startY;
        this.canvas.addEventListener('mousedown', (e) => {
            if (e.button === 0) {
                isDragging = true;
                startX = e.clientX;
                startY = e.clientY;
            }
        });

        window.addEventListener('mousemove', (e) => {
            if (isDragging) {
                const dx = e.clientX - startX;
                const dy = e.clientY - startY;
                startX = e.clientX;
                startY = e.clientY;
                this.scrollX = Math.max(0, this.scrollX - dx);
                this.scrollY = Math.max(0, this.scrollY - dy);
                this.render();
            }
        });

        window.addEventListener('mouseup', () => { isDragging = false; });
    }

    async load(arrayBuffer) {
        const zip = await JSZip.loadAsync(arrayBuffer);

        // 1. Parse Shared Strings
        if (zip.files['xl/sharedStrings.xml']) {
            const ssXml = await zip.files['xl/sharedStrings.xml'].async('text');
            const parser = new DOMParser();
            const ssDoc = parser.parseFromString(ssXml, 'text/xml');
            const siNodes = ssDoc.getElementsByTagName('si');
            this.sharedStrings = [];
            for (let si of siNodes) {
                let text = '';
                const tNodes = si.getElementsByTagName('t');
                for (let t of tNodes) text += t.textContent;
                this.sharedStrings.push(text);
            }
        }

        // 2. Parse Workbook & Sheets
        const wbXml = await zip.files['xl/workbook.xml'].async('text');
        const parser = new DOMParser();
        const wbDoc = parser.parseFromString(wbXml, 'text/xml');
        const sheetNodes = wbDoc.getElementsByTagName('sheet');
        this.sheets = [];
        for (let s of sheetNodes) {
            this.sheets.push({
                name: s.getAttribute('name'),
                id: s.getAttribute('sheetId'),
                rId: s.getAttribute('r:id') || s.getAttribute('id')
            });
        }

        // 3. Parse Worksheet Data (Sheet 1 = REPORT)
        for (let i = 0; i < this.sheets.length; i++) {
            const sName = this.sheets[i].name;
            const path = `xl/worksheets/sheet${i + 1}.xml`;
            if (zip.files[path]) {
                const sXml = await zip.files[path].async('text');
                const sDoc = parser.parseFromString(sXml, 'text/xml');
                this.sheetData[sName] = this.parseSheetXml(sDoc);
            }
        }

        // 4. Parse Scatter Charts from xl/charts/
        for (let path in zip.files) {
            if (path.startsWith('xl/charts/chart') && path.endsWith('.xml')) {
                const cXml = await zip.files[path].async('text');
                const cDoc = parser.parseFromString(cXml, 'text/xml');
                this.charts[path] = this.parseChartXml(cDoc);
            }
        }

        this.activeSheetName = this.sheets.length > 0 ? this.sheets[0].name : 'REPORT';
        this.render();
    }

    parseSheetXml(doc) {
        const cells = {};
        const merges = [];
        const colWidths = {};

        // Parse column widths
        const cols = doc.getElementsByTagName('col');
        for (let c of cols) {
            const min = parseInt(c.getAttribute('min'));
            const max = parseInt(c.getAttribute('max'));
            const width = parseFloat(c.getAttribute('width')) || 10;
            const pxWidth = Math.round(width * 8);
            for (let colIdx = min; colIdx <= max; colIdx++) {
                colWidths[colIdx] = pxWidth;
            }
        }

        // Parse Merged Cells
        const mergeNodes = doc.getElementsByTagName('mergeCell');
        for (let m of mergeNodes) {
            merges.push(m.getAttribute('ref'));
        }

        // Parse Rows & Cells
        const rowNodes = doc.getElementsByTagName('row');
        for (let r of rowNodes) {
            const rIdx = parseInt(r.getAttribute('r'));
            const cNodes = r.getElementsByTagName('c');
            for (let c of cNodes) {
                const ref = c.getAttribute('r');
                const type = c.getAttribute('t');
                const vNode = c.getElementsByTagName('v')[0];
                let val = vNode ? vNode.textContent : '';

                if (type === 's' && val !== '') {
                    val = this.sharedStrings[parseInt(val)] || '';
                }

                cells[ref] = { ref, r: rIdx, val, style: c.getAttribute('s') };
            }
        }

        return { cells, merges, colWidths };
    }

    parseChartXml(doc) {
        const seriesNodes = doc.getElementsByTagName('c:ser');
        const series = [];

        for (let s of seriesNodes) {
            const tx = s.querySelector('c\\:tx c\\:v, tx v');
            const name = tx ? tx.textContent.trim() : 'Series';

            const colorNode = s.querySelector('a\\:solidFill a\\:srgbClr, solidFill srgbClr');
            const colorHex = colorNode ? '#' + colorNode.getAttribute('val') : '#00b0f0';

            const dashNode = s.querySelector('a\\:ln a\\:prstDash, ln prstDash');
            const dash = dashNode ? dashNode.getAttribute('val') : 'solid';

            const xPts = s.querySelectorAll('c\\:xVal c\\:pt, xVal pt');
            const yPts = s.querySelectorAll('c\\:yVal c\\:pt, yVal pt');
            const x = [], y = [];

            for (let p of xPts) {
                const v = p.querySelector('c\\:v, v');
                if (v) x.push(parseFloat(v.textContent));
            }
            for (let p of yPts) {
                const v = p.querySelector('c\\:v, v');
                if (v) y.push(parseFloat(v.textContent));
            }

            series.push({ name, color: colorHex, dash, x, y });
        }

        return { series };
    }

    render() {
        if (!this.ctx) return;
        const ctx = this.ctx;
        ctx.fillStyle = '#ffffff';
        ctx.fillRect(0, 0, this.width, this.height);

        const currentData = this.sheetData[this.activeSheetName];
        if (!currentData) return;

        ctx.save();

        // 1. Draw Grid Lines and Cells
        this.renderGrid(ctx, currentData);

        // 2. Draw In-Sheet Scatter Chart
        if (this.activeSheetName === 'REPORT' && this.charts['xl/charts/chart1.xml']) {
            this.renderChartOverlay(ctx, this.charts['xl/charts/chart1.xml'], 'DIE1 AND DIE 2 VOLTAGE VS ANGLE', 1, 18, 21, 35);
        } else if (this.activeSheetName === 'TORQUE' && this.charts['xl/charts/chart2.xml']) {
            this.renderChartOverlay(ctx, this.charts['xl/charts/chart2.xml'], 'TORQUE CW & CCW VS ANGLE', 1, 18, 12, 35);
        }

        // 3. Draw Sticky Row & Column Headers (A, B, C... and 1, 2, 3...)
        this.renderStickyHeaders(ctx, currentData);

        ctx.restore();
    }

    renderGrid(ctx, data) {
        const { cells, colWidths } = data;
        const startX = this.headerColWidth - this.scrollX;
        const startY = this.headerRowHeight - this.scrollY;

        let currentY = startY;
        for (let r = 1; r <= 100; r++) {
            const rowH = this.defaultRowHeight * this.zoom;
            let currentX = startX;

            for (let c = 1; c <= 22; c++) {
                const colW = (colWidths[c] || this.defaultColWidth) * this.zoom;
                const colLetter = this.getColLetter(c);
                const ref = `${colLetter}${r}`;
                const cell = cells[ref];

                // Background Fills for Special LabVIEW Template Headers
                ctx.fillStyle = '#ffffff';
                if (r === 2) ctx.fillStyle = '#f8fafc';
                else if (r >= 3 && r <= 7 && (c === 2 || c === 11 || c === 18)) ctx.fillStyle = '#f2f2f2';
                else if (ref === 'S5') {
                    const statusStr = cell ? String(cell.val).toUpperCase() : '';
                    ctx.fillStyle = statusStr.includes('PASS') ? '#64ff00' : (statusStr.includes('FAIL') ? '#ff3b30' : '#ffffff');
                } else if (r === 9 || r === 10) {
                    if (c >= 8 && c <= 11) ctx.fillStyle = '#fff2cc';
                    else if (c >= 15 && c <= 18) ctx.fillStyle = '#fce4d6';
                    else ctx.fillStyle = '#e2efda';
                }

                ctx.fillRect(currentX, currentY, colW, rowH);

                // Grid Border
                ctx.strokeStyle = '#d4d4d8';
                ctx.lineWidth = 1;
                ctx.strokeRect(currentX, currentY, colW, rowH);

                // Text Content
                if (cell && cell.val !== '') {
                    ctx.fillStyle = ref === 'S5' ? '#000000' : (r === 2 ? '#002060' : '#1e293b');
                    ctx.font = r === 2 ? `bold ${14 * this.zoom}px Arial` : (r <= 10 ? `bold ${10 * this.zoom}px Arial` : `${10 * this.zoom}px Arial`);
                    ctx.textAlign = (r >= 9 && c >= 3) ? 'right' : 'left';
                    ctx.textBaseline = 'middle';

                    const textX = (r >= 9 && c >= 3) ? currentX + colW - (4 * this.zoom) : currentX + (4 * this.zoom);
                    const textY = currentY + (rowH / 2);

                    ctx.save();
                    ctx.beginPath();
                    ctx.rect(currentX, currentY, colW, rowH);
                    ctx.clip();
                    ctx.fillText(cell.val, textX, textY);
                    ctx.restore();
                }

                currentX += colW;
            }
            currentY += rowH;
        }
    }

    renderChartOverlay(ctx, chartData, title, fromCol, fromRow, toCol, toRow) {
        const startX = this.headerColWidth - this.scrollX;
        const startY = this.headerRowHeight - this.scrollY;

        let cx = startX;
        for (let c = 1; c < fromCol; c++) cx += (this.sheetData[this.activeSheetName].colWidths[c] || this.defaultColWidth) * this.zoom;
        let cy = startY + (fromRow - 1) * this.defaultRowHeight * this.zoom;

        let cw = 0;
        for (let c = fromCol; c <= toCol; c++) cw += (this.sheetData[this.activeSheetName].colWidths[c] || this.defaultColWidth) * this.zoom;
        let ch = (toRow - fromRow + 1) * this.defaultRowHeight * this.zoom;

        // Chart Card Frame
        ctx.fillStyle = '#ffffff';
        ctx.shadowColor = 'rgba(0,0,0,0.15)';
        ctx.shadowBlur = 10;
        ctx.fillRect(cx, cy, cw, ch);
        ctx.shadowBlur = 0;

        ctx.strokeStyle = '#002060';
        ctx.lineWidth = 2;
        ctx.strokeRect(cx, cy, cw, ch);

        // Title
        ctx.fillStyle = '#002060';
        ctx.font = `bold ${12 * this.zoom}px Arial`;
        ctx.textAlign = 'center';
        ctx.fillText(title, cx + (cw / 2), cy + (20 * this.zoom));

        // Plot Box
        const plotMargin = { top: 35 * this.zoom, bottom: 40 * this.zoom, left: 50 * this.zoom, right: 30 * this.zoom };
        const px = cx + plotMargin.left;
        const py = cy + plotMargin.top;
        const pw = cw - plotMargin.left - plotMargin.right;
        const ph = ch - plotMargin.top - plotMargin.bottom;

        ctx.fillStyle = '#fafafa';
        ctx.fillRect(px, py, pw, ph);
        ctx.strokeStyle = '#cbd5e1';
        ctx.lineWidth = 1;
        ctx.strokeRect(px, py, pw, ph);

        // Axes Ticks & Grid Lines
        let minX = 0, maxX = 70, minY = 0, maxY = 5.2;
        ctx.strokeStyle = '#e2e8f0';
        ctx.fillStyle = '#64748b';
        ctx.font = `${9 * this.zoom}px monospace`;
        ctx.textAlign = 'right';

        for (let yVal = 0; yVal <= 5; yVal += 1) {
            const yPos = py + ph - (yVal / maxY) * ph;
            ctx.beginPath();
            ctx.moveTo(px, yPos);
            ctx.lineTo(px + pw, yPos);
            ctx.stroke();
            ctx.fillText(yVal.toFixed(1) + 'V', px - (6 * this.zoom), yPos + 3);
        }

        // Draw Curves
        chartData.series.forEach(ser => {
            if (!ser.x || ser.x.length === 0) return;
            ctx.strokeStyle = ser.color;
            ctx.lineWidth = 2;
            if (ser.dash === 'dash') ctx.setLineDash([4, 4]);
            else ctx.setLineDash([]);

            ctx.beginPath();
            for (let i = 0; i < ser.x.length; i++) {
                const ptX = px + (ser.x[i] / maxX) * pw;
                const ptY = py + ph - (ser.y[i] / maxY) * ph;
                if (i === 0) ctx.moveTo(ptX, ptY);
                else ctx.lineTo(ptX, ptY);
            }
            ctx.stroke();
        });
        ctx.setLineDash([]);
    }

    renderStickyHeaders(ctx, data) {
        const { colWidths } = data;
        const startX = this.headerColWidth - this.scrollX;
        const startY = this.headerRowHeight - this.scrollY;

        // Top Column Header Row (A, B, C...)
        ctx.fillStyle = '#e2e8f0';
        ctx.fillRect(0, 0, this.width, this.headerRowHeight);
        ctx.fillStyle = '#475569';
        ctx.font = `bold 10px Arial`;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';

        let curX = startX;
        for (let c = 1; c <= 22; c++) {
            const colW = (colWidths[c] || this.defaultColWidth) * this.zoom;
            ctx.strokeStyle = '#cbd5e1';
            ctx.strokeRect(curX, 0, colW, this.headerRowHeight);
            ctx.fillText(this.getColLetter(c), curX + (colW / 2), this.headerRowHeight / 2);
            curX += colW;
        }

        // Left Row Header Column (1, 2, 3...)
        ctx.fillStyle = '#e2e8f0';
        ctx.fillRect(0, 0, this.headerColWidth, this.height);
        let curY = startY;
        for (let r = 1; r <= 100; r++) {
            const rowH = this.defaultRowHeight * this.zoom;
            ctx.strokeStyle = '#cbd5e1';
            ctx.strokeRect(0, curY, this.headerColWidth, rowH);
            ctx.fillText(r.toString(), this.headerColWidth / 2, curY + (rowH / 2));
            curY += rowH;
        }

        // Top-Left Header Intersection Corner
        ctx.fillStyle = '#cbd5e1';
        ctx.fillRect(0, 0, this.headerColWidth, this.headerRowHeight);
        ctx.strokeStyle = '#94a3b8';
        ctx.strokeRect(0, 0, this.headerColWidth, this.headerRowHeight);
    }

    getColLetter(colIdx) {
        let temp, letter = '';
        while (colIdx > 0) {
            temp = (colIdx - 1) % 26;
            letter = String.fromCharCode(temp + 65) + letter;
            colIdx = (colIdx - temp - 1) / 26;
        }
        return letter;
    }
}

window.TpsExcelEngine = TpsExcelEngine;
