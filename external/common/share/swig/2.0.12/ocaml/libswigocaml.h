/* Ocaml runtime support */

#ifdef __cplusplus
extern "C" {
#endif

    typedef int oc_bool;
    extern void *nullptr;
    
    extern oc_bool isnull( void *v );
    
    extern void *get_char_ptr( char *str );
    extern void *make_ptr_array( int size );
    extern void *get_ptr( void *arrayptr, int elt );
    extern void set_ptr( void *arrayptr, int elt, void *elt_v );
    extern void *offset_ptr( void *ptr, int n );

#ifdef __cplusplus
};
#endif
