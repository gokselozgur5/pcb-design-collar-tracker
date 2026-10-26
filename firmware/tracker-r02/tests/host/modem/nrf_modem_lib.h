#ifndef COLLAR_HOST_MODEM_H
#define COLLAR_HOST_MODEM_H
struct nrf_modem_fault_info { int unused; };
void nrf_modem_fault_handler(struct nrf_modem_fault_info *);
#endif
