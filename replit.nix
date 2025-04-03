{pkgs}: {
  deps = [
    pkgs.lsof
    pkgs.libGLU
    pkgs.libGL
    pkgs.postgresql
    pkgs.openssl
  ];
}
