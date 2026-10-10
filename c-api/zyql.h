/* zyql.h — ZYQL verified-decision C API, v0.1.0 (SQLite-style core).
 *
 * One .c file, one .h file, zero dependencies. Any language that can
 * call C can decide-and-prove: the API is the bridge, exactly like
 * sqlite3.c is for databases and (as of 2026) Qiskit's C API is for
 * quantum circuits.
 *
 * Honest scope (parity with prototype/nexa_core.py, tested):
 *   - PORTGATE: signed lexical purpose gate, 7 prohibited classes,
 *     refusal BEFORE compute with purpose VERBATIM + SHA-256 digest.
 *   - Families: kepler3, expression (constant fold).
 *   - Certificates carry the same field names and the SAME digests
 *     as the Python core (input_hash, sha256_refusal_digest).
 */
#ifndef ZYQL_H
#define ZYQL_H
#ifdef __cplusplus
extern "C" {
#endif

typedef enum {
    ZYQL_OK = 0,            /* decided (answer is 0 or 1)            */
    ZYQL_REFUSED = 1,       /* refused before compute (answer is -1) */
    ZYQL_ERROR = -1         /* structural error (see message)        */
} zyql_status;

typedef struct zyql_decision zyql_decision;  /* opaque */

/* Parse a NEXA program (ASK / CONTRACT / MODEL blocks) and decide it.
 * Returns a decision object or NULL on out-of-memory. Check status. */
zyql_decision *zyql_decide(const char *program_src);

zyql_status     zyql_result(const zyql_decision *d);   /* ZYQL_*       */
int             zyql_answer(const zyql_decision *d);   /* 1 true, 0 false, -1 null */
const char     *zyql_receipt(const zyql_decision *d);   /* certificate JSON       */
const char     *zyql_message(const zyql_decision *d);  /* error/status message    */
void            zyql_close(zyql_decision *d);

/* Direct gate access (no program needed): prohibited class for a
 * purpose string, or NULL when benign. Same word rules as Python. */
const char     *zyql_purpose_class(const char *purpose);

/* sha256 of bytes, lowercase hex into out (must hold 65 bytes). */
void            zyql_sha256_hex(const void *data, unsigned long len,
                                char out[65]);

#ifdef __cplusplus
}
#endif
#endif /* ZYQL_H */
