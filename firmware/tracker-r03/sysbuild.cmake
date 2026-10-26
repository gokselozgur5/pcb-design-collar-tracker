# Sysbuild's parent USER_CACHE_DIR is not inherited by its child CMake processes.
# Keep both images in the task cache without changing HOME or the SDK checkout.
if(NOT DEFINED USER_CACHE_DIR)
  message(FATAL_ERROR "Pass an explicit task USER_CACHE_DIR")
endif()
get_property(collar_images GLOBAL PROPERTY sysbuild_images)
foreach(collar_image ${collar_images})
  set_property(TARGET ${collar_image} APPEND PROPERTY _EP_CMAKE_ARGS
    "-DUSER_CACHE_DIR:PATH=${USER_CACHE_DIR}")
endforeach()
if(NOT EXISTS "${SB_CONFIG_BOOT_SIGNATURE_KEY_FILE}" OR
   SB_CONFIG_BOOT_SIGNATURE_KEY_FILE MATCHES "/mcuboot/root-")
  message(FATAL_ERROR "Supply an explicit signing key outside the public SDK defaults")
endif()
