import fs from "node:fs/promises";
import path from "node:path";
import { Workbook, SpreadsheetFile } from "@oai/artifact-tool";

const baseDir = process.cwd();
const outputDir = path.join(baseDir, "outputs", "ae_portugues_em_2b_teste");
const inputJson = path.join(outputDir, "dados_ae_portugues_em_2b.json");
const outputXlsx = path.join(outputDir, "planilha_ae_portugues_em_2b_teste.xlsx");

function columnName(index) {
  let n = index + 1;
  let name = "";
  while (n > 0) {
    const rem = (n - 1) % 26;
    name = String.fromCharCode(65 + rem) + name;
    n = Math.floor((n - 1) / 26);
  }
  return name;
}

function toMatrix(rows) {
  if (!rows.length) return [["sem dados"]];
  const headers = Object.keys(rows[0]);
  const matrix = [headers];
  for (const row of rows) {
    matrix.push(
      headers.map((header) => {
        const value = row[header];
        if (Array.isArray(value)) return value.join(" | ");
        if (value === null || value === undefined) return "";
        return value;
      }),
    );
  }
  return { headers, matrix };
}

async function writeSheet(workbook, sheetName, rows) {
  const sheet = workbook.worksheets.add(sheetName);
  const { matrix } = toMatrix(rows);
  const lastCol = columnName(matrix[0].length - 1);
  const lastRow = matrix.length;
  sheet.getRange(`A1:${lastCol}${lastRow}`).values = matrix;
  return sheetName;
}

const raw = await fs.readFile(inputJson, "utf8");
const data = JSON.parse(raw);

const workbook = Workbook.create();
await writeSheet(workbook, "Mapa_por_Aula", data.mapa_por_aula || []);
await writeSheet(workbook, "Entradas_Base", data.entradas_base || []);

const inspectMapa = await workbook.inspect({
  kind: "table",
  range: "Mapa_por_Aula!A1:M12",
  include: "values",
  tableMaxRows: 12,
  tableMaxCols: 13,
});
console.log(inspectMapa.ndjson);

const inspectBase = await workbook.inspect({
  kind: "table",
  range: "Entradas_Base!A1:O12",
  include: "values",
  tableMaxRows: 12,
  tableMaxCols: 15,
});
console.log(inspectBase.ndjson);

await fs.mkdir(outputDir, { recursive: true });
const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(outputXlsx);

console.log(outputXlsx);
