import fabtotum.fabui.macros.general     as general_macros
import fabtotum.fabui.macros.printing    as print_macros
import fabtotum.fabui.macros.milling     as mill_macros
import fabtotum.fabui.macros.scanning    as scan_macros
import fabtotum.fabui.macros.maintenance as maint_macros
import fabtotum.fabui.macros.calibration as calib_macros
import fabtotum.fabui.macros.testing     as test_macros

PRESET_MAP = {
    # General purpose
    "start_up"                      : general_macros.start_up,
    "shutdown"                      : general_macros.shutdown,
    "auto_bed_leveling"             : general_macros.auto_bed_leveling,
#    "jog_setup"                     : general_macros.jog_setup,
    "home_all"                      : general_macros.home_all,
    "probe_down"                    : general_macros.probe_down,
    "probe_up"                      : general_macros.probe_up,
    "raise_bed"                     : general_macros.raise_bed,
    # Print
    "check_pre_print"               : print_macros.check_pre_print,
    "engage_feeder"                 : print_macros.engage_feeder,
    "start_print"                   : print_macros.start_print,
    "end_print_additive"            : print_macros.end_print,
    "end_print_additive_safe_zone"  : print_macros.end_print_additive_safe_zone,
    # Maintenance
    #~ "pre_unload_spool"              : maint_macros.pre_unload_spool,
    #~ "unload_spool"                  : maint_macros.unload_spool,
    #~ "load_spool"                    : maint_macros.load_spool,
    # Milling
    #~ "start_subtractive_print"       : mill_macros.start_subtractive_print,
    #~ "end_print_subtractive"         : mill_macros.end_print_subtractive,
    #~ "safe_zone"                     : mill_macros.safe_zone,
    # Scanning    
    #~ "check_pre_scan"                : scan_macros.check_pre_scan,
    #~ "engage_4axis"                  : scan_macros.engage_4axis,
    #~ "4th_axis_mode"                 : scan_macros.do_4th_axis_mode,   
    #~ "r_scan"                        : scan_macros.rotary_scan,
    #~ "pg_scan"                       : scan_macros.pg_scan,
    #~ "s_scan"                        : scan_macros.sweep_scan,
    #~ "p_scan"                        : scan_macros.probe_scan,
    #~ "end_scan"                      : scan_macros.end_scan,
    # Calibration
    #~ "probe_setup_prepare"           : calib_macros.probe_setup_prepare,
    #~ "probe_setup_calibrate"         : calib_macros.probe_setup_calibrate,
    #~ "raise_bed_no_g27"              : calib_macros.raise_bed_no_g27,
    # Test
    #~ "laser"                         : test_macros.laser,
    #~ "mill"                          : test_macros.mill,
    #~ "blower"                        : test_macros.blower,
    #~ "head_light"                    : test_macros.head_light,
    #~ "g28"                           : test_macros.g28,
    #~ "end_stop"                      : test_macros.end_stop,
    #~ "temperature"                   : test_macros.temperature
}
