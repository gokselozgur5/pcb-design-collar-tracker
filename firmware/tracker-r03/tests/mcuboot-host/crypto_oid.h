/* The pinned Nordic bootutil renamed this include for TF-PSA-Crypto.
 * The upstream host simulator still pins Mbed TLS 3.6. Its OID constants are
 * supplied by the original header; no bootutil checks or crypto code are changed.
 */
#include <mbedtls/oid.h>
