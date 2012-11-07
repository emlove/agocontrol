/*
 Copyright 2008 Daniel Lechner, Andreas Dielacher
 see COPYING and COPYING.LESSER file for details.
*/

#include "TCM120.h"
#include "EnOceanPort.h"

enocean_data_structure create_base_frame() {
	enocean_data_structure returnvalue = enocean_clean_data_structure();
	returnvalue.SYNC_BYTE1 = C_S_BYTE1;
	returnvalue.SYNC_BYTE2 = C_S_BYTE2;
	returnvalue.H_SEQ_LENGTH = C_H_SEQ_TCT | C_LENGTH;
	return returnvalue;
}

enocean_data_structure tcm120_set_idbase(BYTE baseByte0, BYTE baseByte1, BYTE baseByte2, BYTE baseByte3) {
	enocean_data_structure returnvalue = create_base_frame();
	returnvalue.ORG = C_ORG_SET_IDBASE;
	returnvalue.DATA_BYTE3 = baseByte3;
	returnvalue.DATA_BYTE2 = baseByte2;
	returnvalue.DATA_BYTE1 = baseByte1;
	returnvalue.DATA_BYTE0 = baseByte0;
	returnvalue.CHECKSUM = enocean_calc_checksum(returnvalue);
	return returnvalue;
}

enocean_data_structure tcm120_rd_idbase() {
	enocean_data_structure returnvalue = create_base_frame();
	returnvalue.ORG = C_ORG_RD_IDBASE;
	returnvalue.CHECKSUM = enocean_calc_checksum(returnvalue);
	return returnvalue;
}

enocean_data_structure tcm120_set_rx_sensitivity(BYTE sensitivity) {
	enocean_data_structure returnvalue = create_base_frame();
	returnvalue.ORG = C_ORG_SET_RX_SENSITIVITY;
	returnvalue.DATA_BYTE3 = sensitivity;
	returnvalue.CHECKSUM = enocean_calc_checksum(returnvalue);
	return returnvalue;
}

enocean_data_structure tcm120_rd_rx_sensitivity() {
	enocean_data_structure returnvalue = create_base_frame();
	returnvalue.ORG = C_ORG_RD_RX_SENSITIVITY;
	returnvalue.CHECKSUM = enocean_calc_checksum(returnvalue);
	return returnvalue;
}

enocean_data_structure tcm120_sleep() {
	enocean_data_structure returnvalue = create_base_frame();
	returnvalue.ORG = C_ORG_SLEEP;
	returnvalue.CHECKSUM = enocean_calc_checksum(returnvalue);
	return returnvalue;
}

BYTE tcm120_wake() {
	return C_TELEGRAM_WAKE;
}

enocean_data_structure tcm120_reset() {
	enocean_data_structure returnvalue = create_base_frame();
	returnvalue.ORG = C_ORG_RESET;
	returnvalue.CHECKSUM = enocean_calc_checksum(returnvalue);
	return returnvalue;
}

enocean_data_structure tcm120_modem_on(BYTE modemID_msb, BYTE modemID_lsb) {
	enocean_data_structure returnvalue = create_base_frame();
	returnvalue.ORG = C_ORG_MODEM_ON;
	returnvalue.DATA_BYTE3 = modemID_msb;
	returnvalue.DATA_BYTE2 = modemID_lsb;
	returnvalue.CHECKSUM = enocean_calc_checksum(returnvalue);
	return returnvalue;
}

enocean_data_structure tcm120_modem_off() {
	enocean_data_structure returnvalue = create_base_frame();
	returnvalue.ORG = C_ORG_MODEM_OFF;
	returnvalue.CHECKSUM = enocean_calc_checksum(returnvalue);
	return returnvalue;
}

enocean_data_structure tcm120_rd_modem_status() {
	enocean_data_structure returnvalue = create_base_frame();
	returnvalue.ORG = C_ORG_RD_MODEM_STATUS;
	returnvalue.CHECKSUM = enocean_calc_checksum(returnvalue);
	return returnvalue;
}

enocean_data_structure tcm120_rd_sw_ver() {
	enocean_data_structure returnvalue = create_base_frame();
	returnvalue.ORG = C_ORG_RD_SW_VER;
	returnvalue.CHECKSUM = enocean_calc_checksum(returnvalue);
	return returnvalue;
}
