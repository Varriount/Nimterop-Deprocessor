import json
import glob
import signal
from pathlib import Path
from multiprocessing import Pool
from itertools import chain

from deprocessor.steps import *
from deprocessor.regexes import *
from deprocessor.dsl import *


dsl_text = r"""
# Beginning of file
REGEX BOF IS ^(?<!\n) END

# one or more tab/space characters
REGEX spaces IS (?:[ \t]+) END


# Include header files that contain common definitions,
# but that do not include content we want to wrap.
PRE-REPLACE
    ^(?<!\n)
WITH
    #include <minwindef.h>   \n
    #include <apisetcconv.h> \n
    #include <basetyps.h>    \n
    #include <lmcons.h>      \n
END


# Exclude some C plus plus headers
EXCLUDE PATH \\gdiplus.*\.h2
EXCLUDE PATH \\gdiplus.*\.h2


# Remove non-standard C extensions that Nimterop/Treesitter chokes on.
DEFINE somedummymacro            END

DEFINE __stdcall=                END
DEFINE _stdcall=                 END

DEFINE __declspec(x)=            END
DEFINE _declspec(x)=             END

DEFINE _USE_DECLSPECS_FOR_SAL=0  END
DEFINE _USE_ATTRIBUTES_FOR_SAL=0 END

DEFINE CLFSUSER_API=             END
DEFINE __RPC_FAR=                END

# Define GUIDs as constants
DEFINE INITGUID=1                END

# Remove superfluous underscores
STRIP __
STRIP _


# ## Identifier Adjustments ## #

# Remove MIDL prefixes
STRIP PREFIX __MIDL___MIDL_
STRIP PREFIX __MIDL__


# Adjust prefixes with spurious underscores
REPLACE IID__ WITH IID_ END
REPLACE VK__  WITH VK_  END
REPLACE NS_E_AUDIENCE__ WITH NS_E_AUDIENCE_  END


# Adjust suffixes with spurious underscores
REPLACE __NewEnum      WITH _NewEnum      END
REPLACE __NEWENUM      WITH _NEWENUM      END
REPLACE __BASE         WITH _BASE         END
REPLACE __TOP          WITH _TOP          END
REPLACE __FIRST        WITH _FIRST        END
REPLACE __MASK_FLAGS   WITH _MASK_FLAGS   END
REPLACE __NETWORK_TYPE WITH _NETWORK_TYPE END
REPLACE __NETWORK_TYPE WITH _NETWORK_TYPE END


# Adjust common types
REWRITE TOKEN __int64 TO int64 END
REWRITE TOKEN __int32 TO int32 END
REWRITE TOKEN __int16 TO int16 END
REWRITE TOKEN __int8  TO int8  END


# Camel to Uppercase
REWRITE TOKEN WSPData                          TO WSPDATA                         END
REWRITE TOKEN WSAVersion                       TO WSAVERSION                      END
REWRITE TOKEN WSAServiceClassInfoW             TO WSASERVICECLASSINFOW            END
REWRITE TOKEN WSAServiceClassInfoA             TO WSASERVICECLASSINFOA            END
REWRITE TOKEN WSAQuerySetW                     TO WSAQUERYSETW                    END
REWRITE TOKEN WSAQuerySetA                     TO WSAQUERYSETA                    END
REWRITE TOKEN WSAQuerySet2W                    TO WSAQUERYSET2W                   END
REWRITE TOKEN WSAQuerySet2A                    TO WSAQUERYSET2A                   END
REWRITE TOKEN WSANSClassInfoW                  TO WSANSCLASSINFOW                 END
REWRITE TOKEN WSANSClassInfoA                  TO WSANSCLASSINFOA                 END
REWRITE TOKEN WSAEcomparator                   TO WSAECOMPARATOR                  END
REWRITE TOKEN WSAData                          TO WSADATA                         END
REWRITE TOKEN WMWriterStatisticsEx             TO WM_WRITER_STATISTICS_EX         END
REWRITE TOKEN WMWriterStatistics               TO WM_WRITER_STATISTICS            END
REWRITE TOKEN WMUserWebURL                     TO WM_USER_WEB_URL                 END
REWRITE TOKEN WMUserText                       TO WM_USER_TEXT                    END
REWRITE TOKEN WMSynchronisedLyrics             TO WM_SYNCHRONISED_LYRICS          END
REWRITE TOKEN WMStreamTypeInfo                 TO WM_STREAM_TYPE_INFO             END
REWRITE TOKEN WMReaderStatistics               TO WM_READER_STATISTICS            END
REWRITE TOKEN WMReaderClientInfo               TO WM_READER_CLIENTINFO            END
REWRITE TOKEN WMPortNumberRange                TO WM_PORT_NUMBER_RANGE            END
REWRITE TOKEN WMPicture                        TO WM_PICTURE                      END
REWRITE TOKEN WMMediaType                      TO WM_MEDIA_TYPE                   END
REWRITE TOKEN WMLeakyBucketPair                TO WM_LEAKY_BUCKET_PAIR            END
REWRITE TOKEN WMClientPropertiesEx             TO WM_CLIENT_PROPERTIES_EX         END
REWRITE TOKEN WMClientProperties               TO WM_CLIENT_PROPERTIES            END
REWRITE TOKEN WMAddressAccessEntry             TO WM_ADDRESS_ACCESSENTRY          END
REWRITE TOKEN StrTableW                        TO STRTABLEW                       END
REWRITE TOKEN StrTableA                        TO STRTABLEA                       END
REWRITE TOKEN StrEntryW                        TO STRENTRYW                       END
REWRITE TOKEN StrEntryA                        TO STRENTRYA                       END
REWRITE TOKEN SecurityUserData                 TO SECURITY_USER_DATA              END
REWRITE TOKEN PubAppInfo                       TO PUBAPPINFO                      END
REWRITE TOKEN ProxyConfigParams                TO PROXY_CONFIG_PARAMS             END
REWRITE TOKEN PinInfo                          TO PIN_INFO                        END
REWRITE TOKEN PinDirection                     TO PIN_DIRECTION                   END
REWRITE TOKEN pfLogFrame                       TO PFLOGFRAME                      END
REWRITE TOKEN PfFrameType                      TO PFFRAMETYPE                     END
REWRITE TOKEN PfForwardAction                  TO PFFORWARD_ACTION                END
REWRITE TOKEN MP_Type                          TO MP_TYPE                         END
REWRITE TOKEN MMCButton                        TO MMCBUTTON                       END
REWRITE TOKEN MilMatrix3x2D                    TO MIL_MATRIX3X2D                  END
REWRITE TOKEN MFASF_STREAMSELECTORFLAGS        TO MFASF_STREAMSELECTOR_FLAGS      END
REWRITE TOKEN MediaActivityNotifyType          TO MEDIA_ACTIVITY_NOTIFY_TYPE      END
REWRITE TOKEN LdapReferralCallback             TO LDAP_REFERRAL_CALLBACK          END
REWRITE TOKEN IdentityType                     TO IDENTITY_TYPE                   END
REWRITE TOKEN HMAC_Info                        TO HMAC_INFO                       END
REWRITE TOKEN GlobalFilter                     TO GLOBAL_FILTER                   END
REWRITE TOKEN FilterState                      TO FILTER_STATE                    END
REWRITE TOKEN FilterInfo                       TO FILTER_INFO                     END
REWRITE TOKEN EapAttributeType                 TO EAP_ATTRIBUTE_TYPE              END
REWRITE TOKEN EapAttributes                    TO EAP_ATTRIBUTES                  END
REWRITE TOKEN EapAttribute                     TO EAP_ATTRIBUTE                   END
REWRITE TOKEN DtcLu_Xln_Response               TO DTCLUXLNRESPONSE                END
REWRITE TOKEN DtcLu_Xln_Error                  TO DTCLUXLNERROR                   END
REWRITE TOKEN DtcLu_Xln_Confirmation           TO DTCLUXLNCONFIRMATION            END
REWRITE TOKEN DtcLu_Xln                        TO DTCLUXLN                        END
REWRITE TOKEN DtcLu_CompareStates_Response     TO DTCLUCOMPARESTATESRESPONSE      END
REWRITE TOKEN DtcLu_CompareStates_Error        TO DTCLUCOMPARESTATESERROR         END
REWRITE TOKEN DtcLu_CompareStates_Confirmation TO DTCLUCOMPARESTATESCONFIRMATION  END
REWRITE TOKEN DtcLu_CompareState               TO DTCLUCOMPARESTATE               END
REWRITE TOKEN DnsSection                       TO DNS_SECTION                     END
REWRITE TOKEN DnsRecordOptW                    TO DNS_RECORD_OPTW                 END
REWRITE TOKEN DnsRecordOptA                    TO DNS_RECORD_OPTA                 END
REWRITE TOKEN DnsRecordFlags                   TO DNS_RECORD_FLAGS                END
REWRITE TOKEN DnsAddrArray                     TO DNS_ADDR_ARRAY                  END
REWRITE TOKEN DnsAddr                          TO DNS_ADDR                        END
REWRITE TOKEN DMOMediaType                     TO DMO_MEDIA_TYPE                  END
REWRITE TOKEN DiskQuotaUserInformation         TO DISKQUOTA_USER_INFORMATION      END
REWRITE TOKEN D3DPrimCaps                      TO D3DPRIMCAPS                     END
REWRITE TOKEN D3DNTHALDeviceDesc_V2            TO D3DNTHALDEVICEDESC_V2           END
REWRITE TOKEN D3DNTHALDeviceDesc_V1            TO D3DNTHALDEVICEDESC_V1           END
REWRITE TOKEN D3DNTDeviceDesc_V3               TO D3DNTDEVICEDESC_V3              END
REWRITE TOKEN D3DExecuteBufferDesc             TO D3DEXECUTEBUFFERDESC            END
REWRITE TOKEN D3DDeviceDesc                    TO D3DNDEVICEDESC                  END
REWRITE TOKEN ASFFlatSynchronisedLyrics        TO ASF_FLAT_SYNCHRONISED_LYRICS    END
REWRITE TOKEN ASFFlatPicture                   TO ASF_FLAT_PICTURE                END
REWRITE TOKEN AppInfoData                      TO APPINFODATA                     END
REWRITE TOKEN AMMediaType                      TO AM_MEDIA_TYPE                   END
REWRITE TOKEN AM_SEEKING_SeekingFlags          TO AM_SEEKING_SEEKING_FLAGS        END
REWRITE TOKEN AM_SEEKING_SeekingCapabilities   TO AM_SEEKING_SEEKING_CAPABILITIES END
REWRITE TOKEN AllocatorProperties              TO ALLOCATOR_PROPERTIES            END

REWRITE TOKEN DXGI_DDI_CHECK_MULTIPLANE_OVERLAY_SUPPORT_PLANE_INFO TO DXGI_DDI_CHECK_MULTIPLANEOVERLAYSUPPORT_PLANE_INFO END


# Remove underscores
REWRITE TOKEN TT_HITTESTINFOW          TO TTHITTESTINFOW       END
REWRITE TOKEN TT_HITTESTINFOA          TO TTHITTESTINFOA       END
REWRITE TOKEN RB_HITTESTINFO           TO RBHITTESTINFO        END
REWRITE TOKEN NM_UPDOWN                TO NMUPDOWN             END
REWRITE TOKEN HD_LAYOUT                TO HDLAYOUT             END
REWRITE TOKEN HD_HITTESTINFO           TO HDHITTESTINFO        END
REWRITE TOKEN EVRFilterConfig_Prefs    TO EVRFilterConfigPrefs END


# Add underscores
REWRITE TOKEN TRUSTEEW           TO TRUSTEE_W           END                  
REWRITE TOKEN TRUSTEEA           TO TRUSTEE_A           END                  
REWRITE TOKEN PTRUSTEEW          TO PTRUSTEE_W          END
REWRITE TOKEN PTRUSTEEA          TO PTRUSTEE_A          END
REWRITE TOKEN MFASF_INDEXERFLAGS TO MFASF_INDEXER_FLAGS END
REWRITE TOKEN HDITEMW            TO HD_ITEMW            END
REWRITE TOKEN HDITEMA            TO HD_ITEMA            END
REWRITE TOKEN HDITEM             TO HD_ITEM             END
REWRITE TOKEN EXPLICIT_ACCESSW   TO EXPLICIT_ACCESS_W   END
REWRITE TOKEN EXPLICIT_ACCESSA   TO EXPLICIT_ACCESS_A   END
REWRITE TOKEN DOMAINDESC         TO DOMAIN_DESC         END


# Adjust ambiguous identifiers
REPLACE IsNimProc (\b)   WITH $1 END
REPLACE _IS_NIM_PROC(\b)  WITH $1 END
REPLACE IsNimConst (\b)  WITH $1 END
REPLACE _IS_NIM_CONST(\b) WITH $1 END
REPLACE IsNimType (\b)   WITH $1 END
REPLACE _IS_NIM_TYPE(\b)  WITH $1 END
REPLACE IsNimEnum (\b)   WITH $1 END
REPLACE _IS_NIM_ENUM(\b)  WITH $1 END

REWRITE TOKEN WTSClientDisplay                           TO WTSClientDisplayIsNimEnum                              END
REWRITE TOKEN WTSClientAddress                           TO WTSClientAddressIsNimEnum                              END
REWRITE TOKEN WTS_CLIENT_DISPLAY                         TO WTS_CLIENT_DISPLAY_IS_NIM_TYPE                         END
REWRITE TOKEN WTS_CLIENT_ADDRESS                         TO WTS_CLIENT_ADDRESS_IS_NIM_TYPE                         END
REWRITE TOKEN WriteCacheType                             TO WriteCacheTypeIsNim1                                   END
REWRITE TOKEN WRITE_CACHE_TYPE                           TO WRITE_CACHE_TYPE_IS_NIM_2                              END
REWRITE TOKEN WdsTransportProviderShutdown               TO WdsTransportProviderShutdownIsNimProc                  END
REWRITE TOKEN WdsTransportProviderRefreshSettings        TO WdsTransportProviderRefreshSettingsIsNimProc           END
REWRITE TOKEN WdsTransportProviderDumpState              TO WdsTransportProviderDumpStateIsNimProc                 END
REWRITE TOKEN WDS_TRANSPORTPROVIDER_SHUTDOWN             TO WDS_TRANSPORTPROVIDER_SHUTDOWN_IS_NIM_ENUM             END
REWRITE TOKEN WDS_TRANSPORTPROVIDER_REFRESH_SETTINGS     TO WDS_TRANSPORTPROVIDER_REFRESH_SETTINGS_IS_NIM_ENUM     END
REWRITE TOKEN WDS_TRANSPORTPROVIDER_DUMP_STATE           TO WDS_TRANSPORTPROVIDER_DUMP_STATE_IS_NIM_ENUM           END
REWRITE TOKEN VFW_E_INVALIDMEDIATYPE                     TO VFW_E_INVALIDMEDIATYPE_IS_NIM_2                        END
REWRITE TOKEN VFW_E_INVALID_MEDIA_TYPE                   TO VFW_E_INVALID_MEDIA_TYPE_IS_NIM_1                      END
REWRITE TOKEN TrustedDomainSupportedEncryptionTypes      TO TrustedDomainSupportedEncryptionTypesIsNimEnum         END
REWRITE TOKEN TrustedDomainInformationEx                 TO TrustedDomainInformationExIsNimEnum                    END
REWRITE TOKEN TrustedDomainInformationBasic              TO TrustedDomainInformationBasicIsNimEnum                 END
REWRITE TOKEN TrustedDomainFullInformation               TO TrustedDomainFullInformationIsNimEnum                  END
REWRITE TOKEN TrustedDomainAuthInformation               TO TrustedDomainAuthInformationIsNimEnum                  END
REWRITE TOKEN TRUSTED_DOMAIN_SUPPORTED_ENCRYPTION_TYPES  TO TRUSTED_DOMAIN_SUPPORTED_ENCRYPTION_TYPES_IS_NIM_TYPE  END
REWRITE TOKEN TRUSTED_DOMAIN_INFORMATION_EX              TO TRUSTED_DOMAIN_INFORMATION_EX_IS_NIM_TYPE              END
REWRITE TOKEN TRUSTED_DOMAIN_INFORMATION_BASIC           TO TRUSTED_DOMAIN_INFORMATION_BASIC_IS_NIM_TYPE           END
REWRITE TOKEN TRUSTED_DOMAIN_FULL_INFORMATION            TO TRUSTED_DOMAIN_FULL_INFORMATION_IS_NIM_TYPE            END
REWRITE TOKEN TRUSTED_DOMAIN_AUTH_INFORMATION            TO TRUSTED_DOMAIN_AUTH_INFORMATION_IS_NIM_TYPE            END
REWRITE TOKEN TrackMouseEvent                            TO TrackMouseEventIsNimProc                               END
REWRITE TOKEN TRACKMOUSEEVENT                            TO TRACKMOUSEEVENT_IS_NIM_TYPE                            END
REWRITE TOKEN TMRESUME                                   TO TMRESUME_IS_NIM_2                                      END
REWRITE TOKEN TMJOIN                                     TO TMJOIN_IS_NIM_2                                        END
REWRITE TOKEN TM_RESUME                                  TO TM_RESUME_IS_NIM_1                                     END
REWRITE TOKEN TM_JOIN                                    TO TM_JOIN_IS_NIM_1                                       END
REWRITE TOKEN SymAddSourceStream                         TO SymAddSourceStreamIsNimProc                            END
REWRITE TOKEN SYMADDSOURCESTREAM                         TO SYMADDSOURCESTREAM_IS_NIM_TYPE                         END
REWRITE TOKEN StorageDeviceUnsafeShutdownCount           TO StorageDeviceUnsafeShutdownCountIsNimEnum              END
REWRITE TOKEN StorageDeviceNumaProperty                  TO StorageDeviceNumaPropertyIsNimEnum                     END
REWRITE TOKEN StorageDeviceManagementStatus              TO StorageDeviceManagementStatusIsNimEnum                 END
REWRITE TOKEN STORAGE_DEVICE_UNSAFE_SHUTDOWN_COUNT       TO STORAGE_DEVICE_UNSAFE_SHUTDOWN_COUNT_IS_NIM_TYPE       END
REWRITE TOKEN STORAGE_DEVICE_NUMA_PROPERTY               TO STORAGE_DEVICE_NUMA_PROPERTY_IS_NIM_TYPE               END
REWRITE TOKEN STORAGE_DEVICE_MANAGEMENT_STATUS           TO STORAGE_DEVICE_MANAGEMENT_STATUS_IS_NIM_TYPE           END
REWRITE TOKEN SpatialAudioHrtfDirectivityCone            TO SpatialAudioHrtfDirectivityConeIsNimType               END
REWRITE TOKEN SpatialAudioHrtfDirectivityCardioid        TO SpatialAudioHrtfDirectivityCardioidIsNimType           END
REWRITE TOKEN SpatialAudioHrtfDirectivity_Cone           TO SpatialAudioHrtfDirectivity_ConeIsNimEnum              END
REWRITE TOKEN SpatialAudioHrtfDirectivity_Cardioid       TO SpatialAudioHrtfDirectivity_CardioidIsNimEnum          END
REWRITE TOKEN SoundSentry                                TO SoundSentryIsNimProc                                   END
REWRITE TOKEN SOUNDSENTRY                                TO SOUNDSENTRY_IS_NIM_TYPE                                END
REWRITE TOKEN SHARDAPPIDINFO                             TO SHARDAPPIDINFO_IS_NIM_TYPE                             END
REWRITE TOKEN SHARD_APPIDINFO                            TO SHARD_APPIDINFO_IS_NIM_ENUM                            END
REWRITE TOKEN SecpkgWowClientDll                         TO SecpkgWowClientDllIsNimEnum                            END
REWRITE TOKEN SecpkgNego2Info                            TO SecpkgNego2InfoIsNimEnum                               END
REWRITE TOKEN SecpkgMutualAuthLevel                      TO SecpkgMutualAuthLevelIsNimEnum                         END
REWRITE TOKEN SecpkgGssInfo                              TO SecpkgGssInfoIsNimEnum                                 END
REWRITE TOKEN SecpkgExtraOids                            TO SecpkgExtraOidsIsNimEnum                               END
REWRITE TOKEN SecpkgContextThunks                        TO SecpkgContextThunksIsNimEnum                           END
REWRITE TOKEN SECPKG_WOW_CLIENT_DLL                      TO SECPKG_WOW_CLIENT_DLL_IS_NIM_TYPE                      END
REWRITE TOKEN SECPKG_NEGO2_INFO                          TO SECPKG_NEGO2_INFO_IS_NIM_TYPE                          END
REWRITE TOKEN SECPKG_MUTUAL_AUTH_LEVEL                   TO SECPKG_MUTUAL_AUTH_LEVEL_IS_NIM_TYPE                   END
REWRITE TOKEN SECPKG_GSS_INFO                            TO SECPKG_GSS_INFO_IS_NIM_TYPE                            END
REWRITE TOKEN SECPKG_EXTRA_OIDS                          TO SECPKG_EXTRA_OIDS_IS_NIM_TYPE                          END
REWRITE TOKEN SECPKG_CONTEXT_THUNKS                      TO SECPKG_CONTEXT_THUNKS_IS_NIM_TYPE                      END
REWRITE TOKEN ScriptJustify                              TO ScriptJustifyIsNimProc                                 END
REWRITE TOKEN SCRIPT_JUSTIFY                             TO SCRIPT_JUSTIFY_IS_NIM_TYPE                             END
REWRITE TOKEN SceSvcConfigurationInfo                    TO SceSvcConfigurationInfoIsNimEnum                       END
REWRITE TOKEN SceSvcAnalysisInfo                         TO SceSvcAnalysisInfoIsNimEnum                            END
REWRITE TOKEN SCESVC_CONFIGURATION_INFO                  TO SCESVC_CONFIGURATION_INFO_IS_NIM_TYPE                  END
REWRITE TOKEN SCESVC_ANALYSIS_INFO                       TO SCESVC_ANALYSIS_INFO_IS_NIM_TYPE                       END
REWRITE TOKEN QOSSetFlow                                 TO QOSSetFlowIsNimProc                                    END
REWRITE TOKEN QOSQueryFlow                               TO QOSQueryFlowIsNimProc                                  END
REWRITE TOKEN QOSNotifyFlow                              TO QOSNotifyFlowIsNimProc                                 END
REWRITE TOKEN QOS_SET_FLOW                               TO QOS_SET_FLOW_IS_NIM_ENUM                               END
REWRITE TOKEN QOS_QUERY_FLOW                             TO QOS_QUERY_FLOW_IS_NIM_TYPE                             END
REWRITE TOKEN QOS_NOTIFY_FLOW                            TO QOS_NOTIFY_FLOW_IS_NIM_TYPE                            END
REWRITE TOKEN ProcessMemoryExhaustionInfo                TO ProcessMemoryExhaustionInfoIsNimEnum                   END
REWRITE TOKEN ProcessLeapSecondInfo                      TO ProcessLeapSecondInfoIsNimEnum                         END
REWRITE TOKEN PROCESS_MEMORY_EXHAUSTION_INFO             TO PROCESS_MEMORY_EXHAUSTION_INFO_IS_NIM_TYPE             END
REWRITE TOKEN PROCESS_LEAP_SECOND_INFO                   TO PROCESS_LEAP_SECOND_INFO_IS_NIM_TYPE                   END
REWRITE TOKEN PeerDistClientBasicInfo                    TO PeerDistClientBasicInfoIsNimEnum                       END
REWRITE TOKEN PEERDIST_CLIENT_BASIC_INFO                 TO PEERDIST_CLIENT_BASIC_INFO_IS_NIM_TYPE                 END
REWRITE TOKEN OleUpdate                                  TO OleUpdateIsNimProc                                     END
REWRITE TOKEN OLEUIPASTESPECIALW                         TO OLEUIPASTESPECIALWIsNimType                            END
REWRITE TOKEN OleUIPasteSpecialW                         TO OleUIPasteSpecialWIsNimProc                            END
REWRITE TOKEN OLEUIPASTESPECIALW                         TO OLEUIPASTESPECIALW_IS_NIM_TYPE                         END
REWRITE TOKEN OLEUIPASTESPECIALA                         TO OLEUIPASTESPECIALAIsNimType                            END
REWRITE TOKEN OleUIPasteSpecialA                         TO OleUIPasteSpecialAIsNimProc                            END
REWRITE TOKEN OLEUIPASTESPECIALA                         TO OLEUIPASTESPECIALA_IS_NIM_TYPE                         END
REWRITE TOKEN OleUIInsertObjectW                         TO OleUIInsertObjectWIsNimProc                            END
REWRITE TOKEN OLEUIINSERTOBJECTW                         TO OLEUIINSERTOBJECTW_IS_NIM_TYPE                         END
REWRITE TOKEN OleUIInsertObjectA                         TO OleUIInsertObjectAIsNimProc                            END
REWRITE TOKEN OLEUIINSERTOBJECTA                         TO OLEUIINSERTOBJECTA_IS_NIM_TYPE                         END
REWRITE TOKEN OleUIEditLinksW                            TO OleUIEditLinksWIsNimProc                               END
REWRITE TOKEN OLEUIEDITLINKSW                            TO OLEUIEDITLINKSW_IS_NIM_TYPE                            END
REWRITE TOKEN OleUIEditLinksA                            TO OleUIEditLinksAIsNimProc                               END
REWRITE TOKEN OLEUIEDITLINKSA                            TO OLEUIEDITLINKSA_IS_NIM_TYPE                            END
REWRITE TOKEN OleUIConvertW                              TO OleUIConvertWIsNimProc                                 END
REWRITE TOKEN OLEUICONVERTW                              TO OLEUICONVERTW_IS_NIM_TYPE                              END
REWRITE TOKEN OleUIConvertA                              TO OleUIConvertAIsNimProc                                 END
REWRITE TOKEN OLEUICONVERTA                              TO OLEUICONVERTA_IS_NIM_TYPE                              END
REWRITE TOKEN OleUIChangeSourceW                         TO OleUIChangeSourceWIsNimProc                            END
REWRITE TOKEN OLEUICHANGESOURCEW                         TO OLEUICHANGESOURCEW_IS_NIM_TYPE                         END
REWRITE TOKEN OleUIChangeSourceA                         TO OleUIChangeSourceAIsNimProc                            END
REWRITE TOKEN OLEUICHANGESOURCEA                         TO OLEUICHANGESOURCEA_IS_NIM_TYPE                         END
REWRITE TOKEN OleUIChangeIconW                           TO OleUIChangeIconWIsNimProc                              END
REWRITE TOKEN OLEUICHANGEICONW                           TO OLEUICHANGEICONW_IS_NIM_TYPE                           END
REWRITE TOKEN OleUIChangeIconA                           TO OleUIChangeIconAIsNimProc                              END
REWRITE TOKEN OLEUICHANGEICONA                           TO OLEUICHANGEICONA_IS_NIM_TYPE                           END
REWRITE TOKEN OleUIBusyW                                 TO OleUIBusyWIsNimProc                                    END
REWRITE TOKEN OLEUIBUSYW                                 TO OLEUIBUSYW_IS_NIM_TYPE                                 END
REWRITE TOKEN OleUIBusyA                                 TO OleUIBusyAIsNimProc                                    END
REWRITE TOKEN OLEUIBUSYA                                 TO OLEUIBUSYA_IS_NIM_TYPE                                 END
REWRITE TOKEN OleSetData                                 TO OleSetDataIsNimProc                                    END
REWRITE TOKEN OleRequestData                             TO OleRequestDataIsNimProc                                END
REWRITE TOKEN OleRelease                                 TO OleReleaseIsNimProc                                    END
REWRITE TOKEN OleReconnect                               TO OleReconnectIsNimProc                                  END
REWRITE TOKEN OleDelete                                  TO OleDeleteIsNimProc                                     END
REWRITE TOKEN OleClose                                   TO OleCloseIsNimFunc                                      END
REWRITE TOKEN OLE_UPDATE                                 TO OLE_UPDATE_IS_NIM_TYPE                                 END
REWRITE TOKEN OLE_SETDATA                                TO OLE_SETDATA_IS_NIM_ENUM                                END
REWRITE TOKEN OLE_REQUESTDATA                            TO OLE_REQUESTDATA_IS_NIM_ENUM                            END
REWRITE TOKEN OLE_RELEASE                                TO OLE_RELEASE_IS_NIM_CONST                               END
REWRITE TOKEN OLE_RECONNECT                              TO OLE_RECONNECT_IS_NIM_ENUM                              END
REWRITE TOKEN OLE_DELETE                                 TO OLE_DELETE_IS_NIM_ENUM                                 END
REWRITE TOKEN OLE_CLOSE                                  TO OLE_CLOSE_IS_NIM_ENUM                                  END
REWRITE TOKEN NtmsDriveType                              TO NtmsDriveTypeIsNimType                                 END
REWRITE TOKEN NTMS_DRIVE_TYPE                            TO NTMS_DRIVE_TYPE_IS_NIM_ENUM                            END
REWRITE TOKEN MsV1_0Lm20Logon                            TO MsV1_0Lm20LogonIsNimEnum                               END
REWRITE TOKEN MsV1_0InteractiveProfile                   TO MsV1_0InteractiveProfileIsNimEnum                      END
REWRITE TOKEN MsV1_0InteractiveLogon                     TO MsV1_0InteractiveLogonIsNimEnum                        END
REWRITE TOKEN MSV1_0_LM20_LOGON                          TO MSV1_0_LM20_LOGON_IS_NIM_TYPE                          END
REWRITE TOKEN MSV1_0_INTERACTIVE_PROFILE                 TO MSV1_0_INTERACTIVE_PROFILE_IS_NIM_TYPE                 END
REWRITE TOKEN MSV1_0_INTERACTIVE_LOGON                   TO MSV1_0_INTERACTIVE_LOGON_IS_NIM_TYPE                   END
REWRITE TOKEN MQTRANSACTIONAL                            TO MQTRANSACTIONAL_IS_NIM_TYPE                            END
REWRITE TOKEN MQMSGJOURNAL                               TO MQMSGJOURNAL_IS_NIM_TYPE                               END
REWRITE TOKEN MQMSG_JOURNAL                              TO MQMSG_JOURNAL_IS_NIM_ENUM                              END
REWRITE TOKEN MQJOURNAL                                  TO MQJOURNAL_IS_NIM_ENUM                                  END
REWRITE TOKEN MQERROR                                    TO MQERROR_IS_NIM_ENUM                                    END
REWRITE TOKEN MQAUTHENTICATE                             TO MQAUTHENTICATE_IS_NIM_ENUM                             END
REWRITE TOKEN MQ_TRANSACTIONAL                           TO MQ_TRANSACTIONAL_IS_NIM_ENUM                           END
REWRITE TOKEN MQ_JOURNAL                                 TO MQ_JOURNAL_IS_NIM_TYPE                                 END
REWRITE TOKEN MQ_ERROR                                   TO MQ_ERROR_IS_NIM_TYPE                                   END
REWRITE TOKEN MQ_AUTHENTICATE                            TO MQ_AUTHENTICATE_IS_NIM_TYPE                            END
REWRITE TOKEN MI_Uint8                                   TO MI_Uint8IsNimType                                      END
REWRITE TOKEN MI_UINT8                                   TO MI_UINT8_IS_NIM_ENUM                                   END
REWRITE TOKEN MI_Uint64                                  TO MI_Uint64_IS_NIM_TYPE                                  END
REWRITE TOKEN MI_UINT64                                  TO MI_UINT64_IS_NIM_ENUM                                  END
REWRITE TOKEN MI_Uint32                                  TO MI_Uint32_IS_NIM_TYPE                                  END
REWRITE TOKEN MI_UINT32                                  TO MI_UINT32_IS_NIM_ENUM                                  END
REWRITE TOKEN MI_Uint16                                  TO MI_Uint16_IS_NIM_TYPE                                  END
REWRITE TOKEN MI_UINT16                                  TO MI_UINT16_IS_NIM_ENUM                                  END
REWRITE TOKEN MI_StringA                                 TO MI_StringAIsNimType                                    END
REWRITE TOKEN MI_STRINGA                                 TO MI_STRINGA_IS_NIM_ENUM                                 END
REWRITE TOKEN MI_Sint8                                   TO MI_Sint8_IS_NIM_TYPE                                   END
REWRITE TOKEN MI_SINT8                                   TO MI_SINT8_IS_NIM_ENUM                                   END
REWRITE TOKEN MI_Sint64                                  TO MI_Sint64_IS_NIM_TYPE                                  END
REWRITE TOKEN MI_SINT64                                  TO MI_SINT64_IS_NIM_ENUM                                  END
REWRITE TOKEN MI_Sint32                                  TO MI_Sint32_IS_NIM_TYPE                                  END
REWRITE TOKEN MI_SINT32                                  TO MI_SINT32_IS_NIM_ENUM                                  END
REWRITE TOKEN MI_Sint16                                  TO MI_Sint16_IS_NIM_TYPE                                  END
REWRITE TOKEN MI_SINT16                                  TO MI_SINT16_IS_NIM_ENUM                                  END
REWRITE TOKEN MI_ReferenceA                              TO MI_ReferenceAIsNimType                                 END
REWRITE TOKEN MI_REFERENCEA                              TO MI_REFERENCEA_IS_NIM_ENUM                              END
REWRITE TOKEN MI_Real64                                  TO MI_Real64IsNimType                                     END
REWRITE TOKEN MI_REAL64                                  TO MI_REAL64_IS_NIM_ENUM                                  END
REWRITE TOKEN MI_Real32                                  TO MI_Real32IsNimType                                     END
REWRITE TOKEN MI_REAL32                                  TO MI_REAL32_IS_NIM_ENUM                                  END
REWRITE TOKEN MI_InstanceA                               TO MI_InstanceAIsNimType                                  END
REWRITE TOKEN MI_INSTANCEA                               TO MI_INSTANCEA_IS_NIM_ENUM                               END
REWRITE TOKEN MI_Instance                                TO MI_Instance_IS_NIM_TYPE                                END
REWRITE TOKEN MI_INSTANCE                                TO MI_INSTANCE_IS_NIM_ENUM                                END
REWRITE TOKEN MI_Datetime                                TO MI_DatetimeIsNimType                                   END
REWRITE TOKEN MI_DATETIME                                TO MI_DATETIME_IS_NIM_ENUM                                END
REWRITE TOKEN MI_Char16                                  TO MI_Char16_IS_NIM_TYPE                                  END
REWRITE TOKEN MI_CHAR16                                  TO MI_CHAR16_IS_NIM_ENUM                                  END
REWRITE TOKEN MI_Char                                    TO MI_Char_IS_NIM_TYPE                                    END
REWRITE TOKEN MI_CHAR                                    TO MI_CHAR_IS_NIM_ENUM                                    END
REWRITE TOKEN MI_Boolean                                 TO MI_BooleanIsNimType                                    END
REWRITE TOKEN MI_BOOLEAN                                 TO MI_BOOLEAN_IS_NIM_ENUM                                 END
REWRITE TOKEN MFTOPOLOGY_HARDWARE_MODE                   TO MFTOPOLOGY_HARDWARE_MODE_IS_NIM_ENUM                   END
REWRITE TOKEN MFTOPOLOGY_DXVA_MODE                       TO MFTOPOLOGY_DXVA_MODE_IS_NIM_TYPE                       END
REWRITE TOKEN MFMediaKeyStatus                           TO MFMediaKeyStatusIsNim1                                 END
REWRITE TOKEN MF_TOPOLOGY_HARDWARE_MODE                  TO MF_TOPOLOGY_HARDWARE_MODE_IS_NIM_TYPE                  END
REWRITE TOKEN MF_TOPOLOGY_DXVA_MODE                      TO MF_TOPOLOGY_DXVA_MODE_IS_NIM_CONST                     END
REWRITE TOKEN MF_MEDIAKEY_STATUS                         TO MF_MEDIAKEY_STATUS_IS_NIM_2                            END
REWRITE TOKEN MEDIASUBTYPE_X264                          TO MEDIASUBTYPE_X264_IS_NIM_2                             END
REWRITE TOKEN MEDIASUBTYPE_x264                          TO MEDIASUBTYPE_x264_IS_NIM_1                             END
REWRITE TOKEN MEDIASUBTYPE_WVP2                          TO MEDIASUBTYPE_WVP2_IS_NIM_2                             END
REWRITE TOKEN MEDIASUBTYPE_wvp2                          TO MEDIASUBTYPE_wvp2_IS_NIM_1                             END
REWRITE TOKEN MEDIASUBTYPE_WMVR                          TO MEDIASUBTYPE_WMVR_IS_NIM_2                             END
REWRITE TOKEN MEDIASUBTYPE_wmvr                          TO MEDIASUBTYPE_wmvr_IS_NIM_1                             END
REWRITE TOKEN MEDIASUBTYPE_WMVP                          TO MEDIASUBTYPE_WMVP_IS_NIM_2                             END
REWRITE TOKEN MEDIASUBTYPE_wmvp                          TO MEDIASUBTYPE_wmvp_IS_NIM_1                             END
REWRITE TOKEN MEDIASUBTYPE_wmvb                          TO MEDIASUBTYPE_wmvb_IS_NIM_TYPE                          END
REWRITE TOKEN MEDIASUBTYPE_WMVB                          TO MEDIASUBTYPE_WMVB_IS_NIM_ENUM                          END
REWRITE TOKEN MEDIASUBTYPE_WMVA                          TO MEDIASUBTYPE_WMVA_IS_NIM_2                             END
REWRITE TOKEN MEDIASUBTYPE_wmva                          TO MEDIASUBTYPE_wmva_IS_NIM_1                             END
REWRITE TOKEN MEDIASUBTYPE_WMV3                          TO MEDIASUBTYPE_WMV3_IS_NIM_2                             END
REWRITE TOKEN MEDIASUBTYPE_wmv3                          TO MEDIASUBTYPE_wmv3_IS_NIM_1                             END
REWRITE TOKEN MEDIASUBTYPE_WMV2                          TO MEDIASUBTYPE_WMV2_IS_NIM_2                             END
REWRITE TOKEN MEDIASUBTYPE_wmv2                          TO MEDIASUBTYPE_wmv2_IS_NIM_1                             END
REWRITE TOKEN MEDIASUBTYPE_WMV1                          TO MEDIASUBTYPE_WMV1_IS_NIM_2                             END
REWRITE TOKEN MEDIASUBTYPE_wmv1                          TO MEDIASUBTYPE_wmv1_IS_NIM_1                             END
REWRITE TOKEN MEDIASUBTYPE_MPG4                          TO MEDIASUBTYPE_MPG4_IS_NIM_2                             END
REWRITE TOKEN MEDIASUBTYPE_mpg4                          TO MEDIASUBTYPE_mpg4_IS_NIM_1                             END
REWRITE TOKEN MEDIASUBTYPE_MP4S                          TO MEDIASUBTYPE_MP4S_IS_NIM_2                             END
REWRITE TOKEN MEDIASUBTYPE_mp4s                          TO MEDIASUBTYPE_mp4s_IS_NIM_1                             END
REWRITE TOKEN MEDIASUBTYPE_MP43                          TO MEDIASUBTYPE_MP43_IS_NIM_2                             END
REWRITE TOKEN MEDIASUBTYPE_mp43                          TO MEDIASUBTYPE_mp43_IS_NIM_1                             END
REWRITE TOKEN MEDIASUBTYPE_MP42                          TO MEDIASUBTYPE_MP42_IS_NIM_2                             END
REWRITE TOKEN MEDIASUBTYPE_mp42                          TO MEDIASUBTYPE_mp42_IS_NIM_1                             END
REWRITE TOKEN MEDIASUBTYPE_M4S2                          TO MEDIASUBTYPE_M4S2_IS_NIM_2                             END
REWRITE TOKEN MEDIASUBTYPE_m4s2                          TO MEDIASUBTYPE_m4s2_IS_NIM_1                             END
REWRITE TOKEN LsaTokenInformationV3                      TO LsaTokenInformationV3IsNimEnum                         END
REWRITE TOKEN LsaTokenInformationV2                      TO LsaTokenInformationV2IsNimEnum                         END
REWRITE TOKEN LsaTokenInformationV1                      TO LsaTokenInformationV1IsNimEnum                         END
REWRITE TOKEN LsaTokenInformationNull                    TO LsaTokenInformationNullIsNimEnum                       END
REWRITE TOKEN LSA_TOKEN_INFORMATION_V3                   TO LSA_TOKEN_INFORMATION_V3_IS_NIM_TYPE                   END
REWRITE TOKEN LSA_TOKEN_INFORMATION_V2                   TO LSA_TOKEN_INFORMATION_V2_IS_NIM_TYPE                   END
REWRITE TOKEN LSA_TOKEN_INFORMATION_V1                   TO LSA_TOKEN_INFORMATION_V1_IS_NIM_TYPE                   END
REWRITE TOKEN LSA_TOKEN_INFORMATION_NULL                 TO LSA_TOKEN_INFORMATION_NULL_IS_NIM_TYPE                 END
REWRITE TOKEN LINEPROXYREQUEST                           TO LINEPROXYREQUEST_IS_NIM_TYPE                           END
REWRITE TOKEN LINEMONITORTONE                            TO LINEMONITORTONE_IS_NIM_TYPE                            END
REWRITE TOKEN LINECALLINFO                               TO LINECALLINFO_IS_NIM_1                                  END
REWRITE TOKEN LINEAGENTSTATUS                            TO LINEAGENTSTATUS_IS_NIM_TYPE                            END
REWRITE TOKEN LINE_PROXYREQUEST                          TO LINE_PROXYREQUEST_IS_NIM_ENUM                          END
REWRITE TOKEN LINE_MONITORTONE                           TO LINE_MONITORTONE_IS_NIM_ENUM                           END
REWRITE TOKEN LINE_CALLINFO                              TO LINE_CALLINFO_IS_NIM_2                                 END
REWRITE TOKEN LINE_AGENTSTATUS                           TO LINE_AGENTSTATUS_IS_NIM_ENUM                           END
REWRITE TOKEN JetRetrieveColumn                          TO JetRetrieveColumnIsNimProc                             END
REWRITE TOKEN JET_RETRIEVECOLUMN                         TO JET_RETRIEVECOLUMN_IS_NIM_TYPE                         END
REWRITE TOKEN JET_INDEXRANGE                             TO JET_INDEXRANGE_IS_NIM_ENUM                             END
REWRITE TOKEN JET_INDEX_RANGE                            TO JET_INDEX_RANGE_IS_NIM_TYPE                            END
REWRITE TOKEN JET_DbInfoUpgrade                          TO JET_DbInfoUpgradeIsNimEnum                             END
REWRITE TOKEN JET_DBINFOUPGRADE                          TO JET_DBINFOUPGRADE_IS_NIM_TYPE                          END
REWRITE TOKEN JET_DbInfoMisc                             TO JET_DbInfoMiscIsNimEnum                                END
REWRITE TOKEN JET_DBINFOMISC                             TO JET_DBINFOMISC_IS_NIM_TYPE                             END
REWRITE TOKEN IID_IMSImpExpHelpW                         TO IID_IMSImpExpHelpWIsNim1                               END
REWRITE TOKEN IID_IMSImpExpHelp_W                        TO IID_IMSImpExpHelp_WIsNim2                              END
REWRITE TOKEN IID_IMSAdminBaseW                          TO IID_IMSAdminBaseWIsNim1                                END
REWRITE TOKEN IID_IMSAdminBaseSinkW                      TO IID_IMSAdminBaseSinkWIsNim1                            END
REWRITE TOKEN IID_IMSAdminBaseSink_W                     TO IID_IMSAdminBaseSink_WIsNim2                           END
REWRITE TOKEN IID_IMSAdminBase_W                         TO IID_IMSAdminBase_WIsNim2                               END
REWRITE TOKEN IID_IMSAdminBase3W                         TO IID_IMSAdminBase3WIsNim1                               END
REWRITE TOKEN IID_IMSAdminBase3_W                        TO IID_IMSAdminBase3_WIsNim2                              END
REWRITE TOKEN IID_IMSAdminBase2W                         TO IID_IMSAdminBase2WIsNim1                               END
REWRITE TOKEN IID_IMSAdminBase2_W                        TO IID_IMSAdminBase2_WIsNim2                              END
REWRITE TOKEN IID_AsyncIMSAdminBaseSinkW                 TO IID_AsyncIMSAdminBaseSinkWIsNim1                       END
REWRITE TOKEN IID_AsyncIMSAdminBaseSink_W                TO IID_AsyncIMSAdminBaseSink_WIsNim2                      END
REWRITE TOKEN HH_SET_INFOTYPE                            TO HH_SET_INFOTYPE_IS_NIM_TYPE                            END
REWRITE TOKEN HH_SET_INFO_TYPE                           TO HH_SET_INFO_TYPE_IS_NIM_ENUM                           END
REWRITE TOKEN HeapSummary                                TO HeapSummaryIsNimProc                                   END
REWRITE TOKEN HEAP_SUMMARY                               TO HEAP_SUMMARY_IS_NIM_TYPE                               END
REWRITE TOKEN GLshort                                    TO GLshortIsNimType                                       END
REWRITE TOKEN GLbyte                                     TO GLbyteIsNimType                                        END
REWRITE TOKEN GL_SHORT                                   TO GL_SHORT_IS_NIM_ENUM                                   END
REWRITE TOKEN GL_BYTE                                    TO GL_BYTE_IS_NIM_ENUM                                    END
REWRITE TOKEN GEOID                                      TO GEOID_IS_NIM_TYPE                                      END
REWRITE TOKEN GEO_ID                                     TO GEO_ID_IS_NIM_ENUM                                     END
REWRITE TOKEN FileIdType                                 TO FileIdType                                             END
REWRITE TOKEN FILE_ID_TYPE                               TO FILE_ID_TYPE_IS_NIM_TYPE                               END
REWRITE TOKEN EvtRpcLogin                                TO EvtRpcLoginIsNimEnum                                   END
REWRITE TOKEN EVT_RPC_LOGIN                              TO EVT_RPC_LOGIN_IS_NIM_TYPE                              END
REWRITE TOKEN ER_BUS_KEYSTORE_NOT_LOADED                 TO ER_BUS_KEYSTORE_NOT_LOADED_IS_NIM_1                    END
REWRITE TOKEN ER_BUS_KEY_STORE_NOT_LOADED                TO ER_BUS_KEY_STORE_NOT_LOADED_IS_NIM_2                   END
REWRITE TOKEN ENPROTECTED                                TO ENPROTECTED_IS_NIM_TYPE                                END
REWRITE TOKEN ENDROPFILES                                TO ENDROPFILES_IS_NIM_TYPE                                END
REWRITE TOKEN EN_PROTECTED                               TO EN_PROTECTED_IS_NIM_ENUM                               END
REWRITE TOKEN EN_DROPFILES                               TO EN_DROPFILES_IS_NIM_ENUM                               END
REWRITE TOKEN EMRWIDENPATH                               TO EMRWIDENPATH_IS_NIM_TYPE                               END
REWRITE TOKEN EMRSETMETARGN                              TO EMRSETMETARGN_IS_NIM_TYPE                              END
REWRITE TOKEN EMRFLATTENPATH                             TO EMRFLATTENPATH_IS_NIM_TYPE                             END
REWRITE TOKEN EMRENDPATH                                 TO EMRENDPATH_IS_NIM_TYPE                                 END
REWRITE TOKEN EMRCLOSEFIGURE                             TO EMRCLOSEFIGURE_IS_NIM_TYPE                             END
REWRITE TOKEN EMRBEGINPATH                               TO EMRBEGINPATH_IS_NIM_TYPE                               END
REWRITE TOKEN EMRABORTPATH                               TO EMRABORTPATH_IS_NIM_TYPE                               END
REWRITE TOKEN EMR_WIDENPATH                              TO EMR_WIDENPATH_IS_NIM_ENUM                              END
REWRITE TOKEN EMR_SETMETARGN                             TO EMR_SETMETARGN_IS_NIM_ENUM                             END
REWRITE TOKEN EMR_FLATTENPATH                            TO EMR_FLATTENPATH_IS_NIM_ENUM                            END
REWRITE TOKEN EMR_ENDPATH                                TO EMR_ENDPATH_IS_NIM_ENUM                                END
REWRITE TOKEN EMR_CLOSEFIGURE                            TO EMR_CLOSEFIGURE_IS_NIM_ENUM                            END
REWRITE TOKEN EMR_BEGINPATH                              TO EMR_BEGINPATH_IS_NIM_ENUM                              END
REWRITE TOKEN EMR_ABORTPATH                              TO EMR_ABORTPATH                                          END
REWRITE TOKEN EcSubscriptionType                         TO EcSubscriptionTypeIsNimEnum                            END
REWRITE TOKEN EcSubscriptionDeliveryMode                 TO EcSubscriptionDeliveryModeIsNimEnum                    END
REWRITE TOKEN EcSubscriptionCredentialsType              TO EcSubscriptionCredentialsTypeIsNimEnum                 END
REWRITE TOKEN EcSubscriptionContentFormat                TO EcSubscriptionContentFormatIsNimEnum                   END
REWRITE TOKEN EcSubscriptionConfigurationMode            TO EcSubscriptionConfigurationModeIsNimEnum               END
REWRITE TOKEN EC_SUBSCRIPTION_TYPE                       TO EC_SUBSCRIPTION_TYPE_IS_NIM_TYPE                       END
REWRITE TOKEN EC_SUBSCRIPTION_DELIVERY_MODE              TO EC_SUBSCRIPTION_DELIVERY_MODE_IS_NIM_TYPE              END
REWRITE TOKEN EC_SUBSCRIPTION_CREDENTIALS_TYPE           TO EC_SUBSCRIPTION_CREDENTIALS_TYPE_IS_NIM_TYPE           END
REWRITE TOKEN EC_SUBSCRIPTION_CONTENT_FORMAT             TO EC_SUBSCRIPTION_CONTENT_FORMAT_IS_NIM_TYPE             END
REWRITE TOKEN EC_SUBSCRIPTION_CONFIGURATION_MODE         TO EC_SUBSCRIPTION_CONFIGURATION_MODE_IS_NIM_TYPE         END
REWRITE TOKEN EapCredResp                                TO EapCredRespIsNimEnum                                   END
REWRITE TOKEN EapCredReq                                 TO EapCredReqIsNimEnum                                    END
REWRITE TOKEN EapCredLogonResp                           TO EapCredLogonRespIsNimEnum                              END
REWRITE TOKEN EapCredLogonReq                            TO EapCredLogonReqIsNimEnum                               END
REWRITE TOKEN EapCredExpiryResp                          TO EapCredExpiryRespIsNimEnum                             END
REWRITE TOKEN EapCredExpiryReq                           TO EapCredExpiryReqIsNimEnum                              END
REWRITE TOKEN EAP_CRED_RESP                              TO EAP_CRED_RESP_IS_NIM_TYPE                              END
REWRITE TOKEN EAP_CRED_REQ                               TO EAP_CRED_REQ_IS_NIM_TYPE                               END
REWRITE TOKEN EAP_CRED_LOGON_RESP                        TO EAP_CRED_LOGON_RESP_IS_NIM_TYPE                        END
REWRITE TOKEN EAP_CRED_LOGON_REQ                         TO EAP_CRED_LOGON_REQ_IS_NIM_TYPE                         END
REWRITE TOKEN EAP_CRED_EXPIRY_RESP                       TO EAP_CRED_EXPIRY_RESP_IS_NIM_TYPE                       END
REWRITE TOKEN EAP_CRED_EXPIRY_REQ                        TO EAP_CRED_EXPIRY_REQ_IS_NIM_TYPE                        END
REWRITE TOKEN DwmShowContact                             TO DwmShowContactIsNimProc                                END
REWRITE TOKEN DWM_SHOWCONTACT                            TO DWM_SHOWCONTACT_IS_NIM_TYPE                            END
REWRITE TOKEN DsRolePrimaryDomainInfoBasic               TO DsRolePrimaryDomainInfoBasicIsNimEnum                  END
REWRITE TOKEN DsRoleOperationState                       TO DsRoleOperationStateIsNimEnum                          END
REWRITE TOKEN DSROLE_PRIMARY_DOMAIN_INFO_BASIC           TO DSROLE_PRIMARY_DOMAIN_INFO_BASIC_IS_NIM_TYPE           END
REWRITE TOKEN DSROLE_OPERATION_STATE                     TO DSROLE_OPERATION_STATE_IS_NIM_TYPE                     END
REWRITE TOKEN DnsRRSet                                   TO DNS_RRSET                                              END
REWRITE TOKEN DNS_ADDRARRAY                              TO DNS_ADDRARRAY_IS_NIM_ENUM                              END
REWRITE TOKEN DNS_ADDR_ARRAY                             TO DNS_ADDR_ARRAY_IS_NIM_TYPE                             END
REWRITE TOKEN dispidwstcounter                           TO dispidwstcounterIsNim2                                 END
REWRITE TOKEN dispidvideocounter                         TO dispidvideocounterIsNim2                               END
REWRITE TOKEN dispidvideoanalysis                        TO dispidvideoanalysisIsNim2                              END
REWRITE TOKEN dispidvideo_analysis                       TO dispidvideo_analysisIsNim2                             END
REWRITE TOKEN dispidSetAllocator                         TO dispidSetAllocatorIsNim2                               END
REWRITE TOKEN dispidRecordingAttribute                   TO dispidRecordingAttributeIsNim2                         END
REWRITE TOKEN dispidOutput                               TO dispidOutputsIsNim2                                    END
REWRITE TOKEN dispidMixerBitmap                          TO dispidMixerBitmapIsNim2                                END
REWRITE TOKEN dispidMixerBit                             TO dispidMixerBitIsNim2                                END
REWRITE TOKEN dispidKSCat                                TO dispidKSCatIsNim2                                      END
REWRITE TOKEN dispidInputs                               TO dispidInputsIsNim2                                     END
REWRITE TOKEN dispiddataanalysis                         TO dispiddataanalysisIsNim2                               END
REWRITE TOKEN dispiddata_analysis                        TO dispiddata_analysisIsNim2                              END
REWRITE TOKEN dispidCustomCompositorClass                TO dispidCustomCompositorClassIsNim2                      END
REWRITE TOKEN dispidCLSID                                TO dispidCLSIDIsNim2                                      END
REWRITE TOKEN dispidcccounter                            TO dispidcccounterIsNim2                                  END
REWRITE TOKEN dispidaudiocounter                         TO dispidaudiocounterIsNim2                               END
REWRITE TOKEN dispidaudioanalysis                        TO dispidaudioanalysisIsNim2                              END
REWRITE TOKEN dispidaudio_analysis                       TO dispidaudio_analysisIsNim1                             END
REWRITE TOKEN dispid_wstcounter                          TO dispid_wstcounterIsNim1                                END
REWRITE TOKEN dispid_videocounter                        TO dispid_videocounterIsNim1                              END
REWRITE TOKEN dispid_SourceFilter                        TO dispid_SourceFilterIsNim1                              END
REWRITE TOKEN dispid_SetAllocator                        TO dispid_SetAllocatorIsNim1                              END
REWRITE TOKEN dispid_RecordingAttribute                  TO dispid_RecordingAttributeIsNim1                        END
REWRITE TOKEN DISPID_RDPSRAPI_PROP_APPFILTERENABLE       TO DISPID_RDPSRAPI_PROP_APPFILTERENABLED_IS_NIM_1         END
REWRITE TOKEN DISPID_RDPSRAPI_PROP_APPFILTER_ENABLED     TO DISPID_RDPSRAPI_PROP_APPFILTER_ENABLED_IS_NIM_2        END
REWRITE TOKEN dispid_Output                              TO dispid_OutputsIsNim1                                   END
REWRITE TOKEN dispid_MixerBitmap                         TO dispid_MixerBitmapIsNim1                               END
REWRITE TOKEN dispid_MixerBit                            TO dispid_MixerBitIsNim1                               END
REWRITE TOKEN dispid_KSCat                               TO dispid_KSCatIsNim1                                     END
REWRITE TOKEN dispid_Inputs                              TO dispid_InputsIsNim1                                    END
REWRITE TOKEN dispid_CustomCompositorClass               TO dispid_CustomCompositorClassIsNim1                     END
REWRITE TOKEN dispid_CLSID                               TO dispid_CLSIDIsNim1                                     END
REWRITE TOKEN dispid_cccounter                           TO dispid_cccounterIsNim1                                 END
REWRITE TOKEN dispid_audiocounter                        TO dispid_audiocounterIsNim1                              END
REWRITE TOKEN dispid__SourceFilter                       TO dispid__SourceFilterIsNim1                             END
REWRITE TOKEN DBCOLUMNFLAGS                              TO DBCOLUMNFLAGS_IS_NIM_ENUM                              END
REWRITE TOKEN DBCOLUMN_FLAGS                             TO DBCOLUMN_FLAGS_IS_NIM_TYPE                             END
REWRITE TOKEN D3D12_MESSAGE_ID_UNMAP_INVALIDSUBRESOURCE  TO D3D12_MESSAGE_ID_UNMAP_INVALIDSUBRESOURCE_IS_NIM_1     END
REWRITE TOKEN D3D12_MESSAGE_ID_UNMAP_INVALID_SUBRESOURCE TO D3D12_MESSAGE_ID_UNMAP_INVALID_SUBRESOURCE_IS_NIM_2    END
REWRITE TOKEN D3D12_MESSAGE_ID_MAP_INVALIDSUBRESOURCE    TO D3D12_MESSAGE_ID_MAP_INVALIDSUBRESOURCE_IS_NIM_1       END
REWRITE TOKEN D3D12_MESSAGE_ID_MAP_INVALID_SUBRESOURCE   TO D3D12_MESSAGE_ID_MAP_INVALID_SUBRESOURCE_IS_NIM_2      END
REWRITE TOKEN D3D12_MESSAGE_ID_LIVE_CRYPTOSESSION        TO D3D12_MESSAGE_ID_LIVE_CRYPTOSESSION_IS_NIM_2           END
REWRITE TOKEN D3D12_MESSAGE_ID_LIVE_CRYPTO_SESSION       TO D3D12_MESSAGE_ID_LIVE_CRYPTO_SESSION_IS_NIM_1          END
REWRITE TOKEN D3D12_MESSAGE_ID_DESTROY_CRYPTOSESSION     TO D3D12_MESSAGE_ID_DESTROY_CRYPTOSESSION_IS_NIM_2        END
REWRITE TOKEN D3D12_MESSAGE_ID_DESTROY_CRYPTO_SESSION    TO D3D12_MESSAGE_ID_DESTROY_CRYPTO_SESSION_IS_NIM_1       END
REWRITE TOKEN D3D12_MESSAGE_ID_CREATE_CRYPTOSESSION      TO D3D12_MESSAGE_ID_CREATE_CRYPTOSESSION_IS_NIM_2         END
REWRITE TOKEN D3D12_MESSAGE_ID_CREATE_CRYPTO_SESSION     TO D3D12_MESSAGE_ID_CREATE_CRYPTO_SESSION_IS_NIM_1        END
REWRITE TOKEN CryptImportKey                             TO CryptImportKeyIsNimProc                                END
REWRITE TOKEN CryptExportKey                             TO CryptExportKeyIsNimProc                                END
REWRITE TOKEN CryptEncrypt                               TO CryptEncryptIsNimProc                                  END
REWRITE TOKEN CryptDestroyKey                            TO CryptDestroyKeyIsNimProc                               END
REWRITE TOKEN CryptDecrypt                               TO CryptDecryptIsNimProc                                  END
REWRITE TOKEN CRYPT_IMPORT_KEY                           TO CRYPT_IMPORT_KEY_IS_NIM_ENUM                           END
REWRITE TOKEN CRYPT_EXPORT_KEY                           TO CRYPT_EXPORT_KEY_IS_NIM_ENUM                           END
REWRITE TOKEN CRYPT_ENCRYPT                              TO CRYPT_ENCRYPT_IS_NIM_ENUM                              END
REWRITE TOKEN CRYPT_DESTROYKEY                           TO CRYPT_DESTROYKEY_IS_NIM_ENUM                           END
REWRITE TOKEN CRYPT_DECRYPT                              TO CRYPT_DECRYPT_IS_NIM_ENUM                              END
REWRITE TOKEN CredsspCredEx                              TO CredsspCredExIsNimEnum                                 END
REWRITE TOKEN CREDSSP_CRED_EX                            TO CREDSSP_CRED_EX_IS_NIM_TYPE                            END
REWRITE TOKEN ChooseFontW                                TO ChooseFontWIsNimProc                                   END
REWRITE TOKEN CHOOSEFONTW                                TO CHOOSEFONTW_IS_NIM_TYPE                                END
REWRITE TOKEN ChooseFontA                                TO ChooseFontAIsNimProc                                   END
REWRITE TOKEN CHOOSEFONTA                                TO CHOOSEFONTA_IS_NIM_TYPE                                END
REWRITE TOKEN ChooseColorW                               TO ChooseColorWIsNimProc                                  END
REWRITE TOKEN CHOOSECOLORW                               TO CHOOSECOLORW_IS_NIM_TYPE                               END
REWRITE TOKEN ChooseColorA                               TO ChooseColorAIsNimProc                                  END
REWRITE TOKEN CHOOSECOLORA                               TO CHOOSECOLORA_IS_NIM_TYPE                               END
REWRITE TOKEN CabInfoW                                   TO CABINFOW                                               END
REWRITE TOKEN CabInfoA                                   TO CABINFOA                                               END
REWRITE TOKEN AsnTimeticks                               TO AsnTimeticksIsNimType                                  END
REWRITE TOKEN AsnSequence                                TO AsnSequenceIsNimType                                   END
REWRITE TOKEN AsnOpaque                                  TO AsnOpaqueIsNimType                                     END
REWRITE TOKEN AsnOctetString                             TO AsnOctetStringIsNimType                                END
REWRITE TOKEN AsnObjectIdentifier                        TO AsnObjectIdentifierIsNimType                           END
REWRITE TOKEN AsnIPAddress                               TO AsnIPAddressIsNimType                                  END
REWRITE TOKEN AsnInteger32                               TO AsnInteger32IsNimType                                  END
REWRITE TOKEN AsnGauge32                                 TO AsnGauge32IsNimType                                    END
REWRITE TOKEN AsnCounter64                               TO AsnCounter64IsNimType                                  END
REWRITE TOKEN AsnCounter32                               TO AsnCounter32IsNimType                                  END
REWRITE TOKEN AsnBits                                    TO AsnBitsIsNimType                                       END
REWRITE TOKEN ASN_TIMETICKS                              TO ASN_TIMETICKS_IS_NIM_ENUM                              END
REWRITE TOKEN ASN_SEQUENCE                               TO ASN_SEQUENCE_IS_NIM_ENUM                               END
REWRITE TOKEN ASN_OPAQUE                                 TO ASN_OPAQUE_IS_NIM_ENUM                                 END
REWRITE TOKEN ASN_OCTETSTRING                            TO ASN_OCTETSTRING_IS_NIM_ENUM                            END
REWRITE TOKEN ASN_OBJECTIDENTIFIER                       TO ASN_OBJECTIDENTIFIER_IS_NIM_ENUM                       END
REWRITE TOKEN ASN_IPADDRESS                              TO ASN_IPADDRESS_IS_NIM_ENUM                              END
REWRITE TOKEN ASN_INTEGER32                              TO ASN_INTEGER32_IS_NIM_ENUM                              END
REWRITE TOKEN ASN_GAUGE32                                TO ASN_GAUGE32_IS_NIM_ENUM                                END
REWRITE TOKEN ASN_COUNTER64                              TO ASN_COUNTER64_IS_NIM_ENUM                              END
REWRITE TOKEN ASN_COUNTER32                              TO ASN_COUNTER32_IS_NIM_ENUM                              END
REWRITE TOKEN ASN_BITS                                   TO ASN_BITS_IS_NIM_ENUM                                   END
"""


def worker(dsl, paths):
    # Read files in
    file_data = read_files(paths)

    # Perform initial replacements
    file_data = sub_file_data(dsl.pre_replacements, file_data)

    # Write files out
    write_files(file_data)

    # Run Nimterop over files
    nim_paths = nimterop_files(
        paths          = paths,
        defines        = dsl.defines,
        undefines      = dsl.undefines,
        suffixes       = dsl.suffixes,
        prefixes       = dsl.prefixes,
        type_map       = dsl.type_map,
        identifier_map = dsl.identifier_map,
    )

    # Read files in
    file_data = read_files(nim_paths)

    # Perform post replacements
    file_data = sub_file_data(dsl.post_replacements, file_data)

    # Write files out
    write_files(file_data)


def get_paths(parent_path):
    header_glob = os.path.join(parent_path, '**/*.h2')
    for path in glob.iglob(header_glob, recursive=True):
        invalid = any(
            regex.search(path)
            for regex in dsl.exclude_paths
        )
        if invalid:
            continue

        yield path


if __name__ == "__main__":
    # Parse the directives
    dsl = DSL(dsl_text)

    # Get the paths
    path_list = list(get_paths('./output'))

    # Split the paths into chunks
    chunk_size = 200
    path_chunks = [
        path_list[i:i + chunk_size]
        for i in range(0, len(path_list), chunk_size)
    ]
    
    # Start the pool, using masks to correctly handle ctrl+c
    original_handler = signal.signal(signal.SIGINT, signal.SIG_IGN)
    pool = Pool(4)
    signal.signal(signal.SIGINT, original_handler)

    try:
        print("Running workers")
        pool.starmap(
            worker,
            ((dsl, chunk) for chunk in path_chunks)
        )
    except KeyboardInterrupt:
        print("Caught KeyboardInterrupt, terminating workers")
        pool.terminate()
    else:
        pool.close()