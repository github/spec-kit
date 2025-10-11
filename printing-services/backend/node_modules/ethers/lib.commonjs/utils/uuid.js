"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.uuidV4 = void 0;
/**
 *  Explain UUID and link to RFC here.
 *
 *  @_subsection: api/utils:UUID  [about-uuid]
 */
const data_js_1 = require("./data.js");
/**
 *  Returns the version 4 [[link-uuid]] for the %%randomBytes%%.
 *
 *  @see: https://www.ietf.org/rfc/rfc4122.txt (Section 4.4)
 */
function uuidV4(randomBytes) {
    const bytes = (0, data_js_1.getBytes)(randomBytes, "randomBytes");
    // Section: 4.1.3:
    // - time_hi_and_version[12:16] = 0b0100
    bytes[6] = (bytes[6] & 0x0f) | 0x40;
    // Section 4.4
    // - clock_seq_hi_and_reserved[6] = 0b0
    // - clock_seq_hi_and_reserved[7] = 0b1
    bytes[8] = (bytes[8] & 0x3f) | 0x80;
    const value = (0, data_js_1.hexlify)(bytes);
    return [
        value.substring(2, 10),
        value.substring(10, 14),
        value.substring(14, 18),
        value.substring(18, 22),
        value.substring(22, 34),
    ].join("-");
}
exports.uuidV4 = uuidV4;
//# sourceMappingURL=uuid.js.map