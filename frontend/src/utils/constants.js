// src/utils/constants.js
export const REPORT_TYPES = {
  executive: 'Ejecutivo',
  detailed: 'Detallado', 
  summary: 'Resumen',
  custom: 'Personalizado',
};

export const REPORT_STATUS = {
  generating: 'Generando',
  completed: 'Completado',
  failed: 'Fallido',
  expired: 'Expirado',
};

export const CSV_STATUS = {
  pending: 'Pendiente',
  processing: 'Procesando',
  completed: 'Completado',
  failed: 'Fallido',
};

export const FILE_TYPES = {
  csv: 'CSV',
  pdf: 'PDF',
  image: 'Imagen',
  document: 'Documento',
  other: 'Otro',
};

export const ACTIVITY_TYPES = {
  login: 'Inicio de sesión',
  logout: 'Cierre de sesión',
  upload_csv: 'Subida de CSV',
  generate_report: 'Generación de reporte',
  download_report: 'Descarga de reporte',
  view_dashboard: 'Ver dashboard',
  api_call: 'Llamada API',
};