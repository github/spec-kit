// Shim definition to export a namespace. Cypress is actually a global module
// so import/export isn't allowed there. We import here and define a global module
// so that Cypress can get and use the Blob type

// tslint:disable-next-line:no-implicit-dependencies
import * as blobUtil from 'blob-util'

export = BlobUtil
export as namespace BlobUtil

declare namespace BlobUtil {
  type BlobUtilStatic = typeof blobUtil
}
