#define gh_append2(a, b) scm_append(scm_listify(a, b, SCM_UNDEFINED)) 
#define gh_apply(a, b) scm_apply(a, b, SCM_EOL) 
#define gh_bool2scm SCM_BOOL 
#define gh_boolean_p SCM_BOOLP 
#define gh_car SCM_CAR 
#define gh_cdr SCM_CDR 
#define gh_cons scm_cons 
#define gh_double2scm scm_make_real 
#define gh_int2scm scm_long2num 
#define gh_length(lst) scm_num2ulong(scm_length(lst), SCM_ARG1, FUNC_NAME) 
#define gh_list scm_listify 
#define gh_list_to_vector scm_vector 
#define gh_make_vector scm_make_vector 
#define gh_null_p SCM_NULLP 
#define gh_number_p SCM_NUMBERP 
#define gh_pair_p SCM_CONSP 
#define gh_scm2bool SCM_NFALSEP
#define gh_scm2char SCM_CHAR 
#define gh_scm2double(a) scm_num2dbl(a, FUNC_NAME) 
#define gh_scm2int(a) scm_num2int(a, SCM_ARG1, FUNC_NAME) 
#define gh_scm2long(a) scm_num2long(a, SCM_ARG1, FUNC_NAME) 
#define gh_scm2short(a) scm_num2short(a, SCM_ARG1, FUNC_NAME)
#define gh_scm2newstr SWIG_Guile_scm2newstr
#define gh_scm2ulong(a) scm_num2ulong(a, SCM_ARG1, FUNC_NAME)
#define gh_scm2ushort(a) scm_num2ushort(a, SCM_ARG1, FUNC_NAME)
#define gh_scm2uint(a) scm_num2uint(a, SCM_ARG1, FUNC_NAME)
#define gh_ulong2scm scm_ulong2num
#define gh_long2scm scm_long2num
#define gh_str02scm scm_makfrom0str 
#define gh_long_long2scm scm_long_long2num
#define gh_scm2long_long(a) scm_num2long_long(a, SCM_ARG1, FUNC_NAME)
#define gh_ulong_long2scm scm_ulong_long2num
#define gh_scm2ulong_long(a) scm_num2ulong_long(a, SCM_ARG1, FUNC_NAME)
#define gh_string_p SCM_STRINGP 
#define gh_vector_length SCM_VECTOR_LENGTH 
#define gh_vector_p SCM_VECTORP 
#define gh_vector_ref scm_vector_ref 
#define gh_vector_set_x scm_vector_set_x 
#define gh_char2scm SCM_MAKE_CHAR
