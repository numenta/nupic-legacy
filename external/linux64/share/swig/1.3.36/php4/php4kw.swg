/* -----------------------------------------------------------------------------
 * See the LICENSE file for information on copyright, usage and redistribution
 * of SWIG, and the README file for authors - http://www.swig.org/release.html.
 *
 * php4kw.swg
 *
 * The 'keywords' in PHP are global, ie, the following names are fine
 * when used as class methods.
 * ----------------------------------------------------------------------------- */

#define PHPKW(x) %keywordwarn("'" `x` "' is a php keyword, renamed as 'c_" `x` "'",sourcefmt="%(lower)s", rename="c_%s",fullname=1)  `x`

%define PHPCN(x) 
%keywordwarn("'" `x` "' is a php reserved class name, class renamed as 'c_" `x` "'",%$isclass,rename="c_%s") `x`;
%keywordwarn("'" `x` "' is a php reserved class name, constructor renamed as 'c_" `x` "'",%$isconstructor,rename="c_%s") `x`;
%enddef

#define PHPBN1(x) %builtinwarn("'" `x` "' conflicts with a built-in name in php",sourcefmt="%(lower)s",fullname=1)  `x`
#define PHPBN2(x) %builtinwarn("'" `x` "' conflicts with a built-in name in php")  "::" `x`


/*
   From

     http://aspn.activestate.com/ASPN/docs/PHP/reserved.html

   and reviewed by Olly Betts.

   Further updates from the PHP manual on php.net.
*/

/* We classify these as kw since PHP will not run if used globally. */
/* case insensitive */
PHPKW(and);
PHPKW(array);
PHPKW(as);
PHPKW(break);
PHPKW(case);
PHPKW(cfunction); /* No longer reserved in PHP5 */
PHPKW(class);
PHPKW(const);
PHPKW(continue);
PHPKW(declare);
PHPKW(default);
PHPKW(die);
PHPKW(do);
PHPKW(echo);
PHPKW(else);
PHPKW(elseif);
PHPKW(empty);
PHPKW(enddeclare);
PHPKW(endfor);
PHPKW(endforeach);
PHPKW(endif);
PHPKW(endswitch);
PHPKW(endwhile);
PHPKW(eval);
PHPKW(exit);
PHPKW(extends);
PHPKW(for);
PHPKW(foreach);
PHPKW(function);
PHPKW(global);
PHPKW(if);
PHPKW(include);
PHPKW(include_once);
PHPKW(isset);
PHPKW(list);
PHPKW(new);
PHPKW(old_function); /* No longer reserved in PHP5 */
PHPKW(or);
PHPKW(print);
PHPKW(require);
PHPKW(require_once);
PHPKW(return);
PHPKW(static);
PHPKW(switch);
PHPKW(unset);
PHPKW(use);
PHPKW(var);
PHPKW(while);
PHPKW(xor);
PHPKW(__FILE__);
PHPKW(__LINE__);
PHPKW(__FUNCTION__);
PHPKW(__CLASS__);

/* Added in PHP5 */
PHPKW(__halt_compiler);
PHPKW(abstract);
PHPKW(catch);
PHPKW(clone);
PHPKW(final);
PHPKW(implements);
PHPKW(instanceof);
PHPKW(interface);
PHPKW(private);
PHPKW(protected);
PHPKW(public);
PHPKW(throw);
PHPKW(try);
PHPKW(__METHOD__);

/* We classify these as built-in names since they conflict, but PHP still runs */

/* Type 1: case insensitive */
PHPBN1(__sleep);
PHPBN1(__wakeup);
PHPBN1(not);
PHPBN1(parent);
PHPBN1(virtual);
PHPBN1(NULL);
PHPBN1(TRUE);
PHPBN1(FALSE);

/* Type 2: case sensitive */
/* "Core Predefined Constants" from http://uk2.php.net/manual/en/reserved.constants.php */
PHPBN2(E_ALL);
PHPBN2(E_ERROR);
PHPBN2(E_PARSE);
PHPBN2(E_WARNING);
PHPBN2(E_NOTICE);
PHPBN2(E_CORE_ERROR);
PHPBN2(E_CORE_WARNING);
PHPBN2(E_COMPILE_ERROR);
PHPBN2(E_COMPILE_WARNING);
PHPBN2(E_USER_ERROR);
PHPBN2(E_USER_WARNING);
PHPBN2(E_USER_NOTICE);
PHPBN2(PHP_OS);
PHPBN2(PHP_VERSION);
PHPBN2(PHP_SAPI);
PHPBN2(PHP_EOL);
PHPBN2(PHP_INT_MAX);
PHPBN2(PHP_INT_SIZE);
PHPBN2(DEFAULT_INCLUDE_PATH);
PHPBN2(PEAR_INSTALL_DIR);
PHPBN2(PEAR_EXTENSION_DIR);
PHPBN2(PHP_EXTENSION_DIR);
PHPBN2(PHP_PREFIX);
PHPBN2(PHP_BINDIR);
PHPBN2(PHP_LIBDIR);
PHPBN2(PHP_DATADIR);
PHPBN2(PHP_SYSCONFDIR);
PHPBN2(PHP_LOCALSTATEDIR);
PHPBN2(PHP_CONFIG_FILE_PATH);
PHPBN2(PHP_CONFIG_FILE_SCAN_DIR);
PHPBN2(PHP_SHLIB_SUFFIX);
PHPBN2(PHP_OUTPUT_HANDLER_START);
PHPBN2(PHP_OUTPUT_HANDLER_CONT);
PHPBN2(PHP_OUTPUT_HANDLER_END);
/* "Standard Predefined Constants" from http://uk2.php.net/manual/en/reserved.constants.php */
PHPBN2(EXTR_OVERWRITE);
PHPBN2(EXTR_SKIP);
PHPBN2(EXTR_PREFIX_SAME);
PHPBN2(EXTR_PREFIX_ALL);
PHPBN2(EXTR_PREFIX_INVALID);
PHPBN2(EXTR_PREFIX_IF_EXISTS);
PHPBN2(EXTR_IF_EXISTS);
PHPBN2(SORT_ASC);
PHPBN2(SORT_DESC);
PHPBN2(SORT_REGULAR);
PHPBN2(SORT_NUMERIC);
PHPBN2(SORT_STRING);
PHPBN2(CASE_LOWER);
PHPBN2(CASE_UPPER);
PHPBN2(COUNT_NORMAL);
PHPBN2(COUNT_RECURSIVE);
PHPBN2(ASSERT_ACTIVE);
PHPBN2(ASSERT_CALLBACK);
PHPBN2(ASSERT_BAIL);
PHPBN2(ASSERT_WARNING);
PHPBN2(ASSERT_QUIET_EVAL);
PHPBN2(CONNECTION_ABORTED);
PHPBN2(CONNECTION_NORMAL);
PHPBN2(CONNECTION_TIMEOUT);
PHPBN2(INI_USER);
PHPBN2(INI_PERDIR);
PHPBN2(INI_SYSTEM);
PHPBN2(INI_ALL);
PHPBN2(M_E);
PHPBN2(M_LOG2E);
PHPBN2(M_LOG10E);
PHPBN2(M_LN2);
PHPBN2(M_LN10);
PHPBN2(M_PI);
PHPBN2(M_PI_2);
PHPBN2(M_PI_4);
PHPBN2(M_1_PI);
PHPBN2(M_2_PI);
PHPBN2(M_2_SQRTPI);
PHPBN2(M_SQRT2);
PHPBN2(M_SQRT1_2);
PHPBN2(CRYPT_SALT_LENGTH);
PHPBN2(CRYPT_STD_DES);
PHPBN2(CRYPT_EXT_DES);
PHPBN2(CRYPT_MD5);
PHPBN2(CRYPT_BLOWFISH);
PHPBN2(DIRECTORY_SEPARATOR);
PHPBN2(SEEK_SET);
PHPBN2(SEEK_CUR);
PHPBN2(SEEK_END);
PHPBN2(LOCK_SH);
PHPBN2(LOCK_EX);
PHPBN2(LOCK_UN);
PHPBN2(LOCK_NB);
PHPBN2(HTML_SPECIALCHARS);
PHPBN2(HTML_ENTITIES);
PHPBN2(ENT_COMPAT);
PHPBN2(ENT_QUOTES);
PHPBN2(ENT_NOQUOTES);
PHPBN2(INFO_GENERAL);
PHPBN2(INFO_CREDITS);
PHPBN2(INFO_CONFIGURATION);
PHPBN2(INFO_MODULES);
PHPBN2(INFO_ENVIRONMENT);
PHPBN2(INFO_VARIABLES);
PHPBN2(INFO_LICENSE);
PHPBN2(INFO_ALL);
PHPBN2(CREDITS_GROUP);
PHPBN2(CREDITS_GENERAL);
PHPBN2(CREDITS_SAPI);
PHPBN2(CREDITS_MODULES);
PHPBN2(CREDITS_DOCS);
PHPBN2(CREDITS_FULLPAGE);
PHPBN2(CREDITS_QA);
PHPBN2(CREDITS_ALL);
PHPBN2(STR_PAD_LEFT);
PHPBN2(STR_PAD_RIGHT);
PHPBN2(STR_PAD_BOTH);
PHPBN2(PATHINFO_DIRNAME);
PHPBN2(PATHINFO_BASENAME);
PHPBN2(PATHINFO_EXTENSION);
PHPBN2(PATH_SEPARATOR);
PHPBN2(CHAR_MAX);
PHPBN2(LC_CTYPE);
PHPBN2(LC_NUMERIC);
PHPBN2(LC_TIME);
PHPBN2(LC_COLLATE);
PHPBN2(LC_MONETARY);
PHPBN2(LC_ALL);
PHPBN2(LC_MESSAGES);
PHPBN2(ABDAY_1);
PHPBN2(ABDAY_2);
PHPBN2(ABDAY_3);
PHPBN2(ABDAY_4);
PHPBN2(ABDAY_5);
PHPBN2(ABDAY_6);
PHPBN2(ABDAY_7);
PHPBN2(DAY_1);
PHPBN2(DAY_2);
PHPBN2(DAY_3);
PHPBN2(DAY_4);
PHPBN2(DAY_5);
PHPBN2(DAY_6);
PHPBN2(DAY_7);
PHPBN2(ABMON_1);
PHPBN2(ABMON_2);
PHPBN2(ABMON_3);
PHPBN2(ABMON_4);
PHPBN2(ABMON_5);
PHPBN2(ABMON_6);
PHPBN2(ABMON_7);
PHPBN2(ABMON_8);
PHPBN2(ABMON_9);
PHPBN2(ABMON_10);
PHPBN2(ABMON_11);
PHPBN2(ABMON_12);
PHPBN2(MON_1);
PHPBN2(MON_2);
PHPBN2(MON_3);
PHPBN2(MON_4);
PHPBN2(MON_5);
PHPBN2(MON_6);
PHPBN2(MON_7);
PHPBN2(MON_8);
PHPBN2(MON_9);
PHPBN2(MON_10);
PHPBN2(MON_11);
PHPBN2(MON_12);
PHPBN2(AM_STR);
PHPBN2(PM_STR);
PHPBN2(D_T_FMT);
PHPBN2(D_FMT);
PHPBN2(T_FMT);
PHPBN2(T_FMT_AMPM);
PHPBN2(ERA);
PHPBN2(ERA_YEAR);
PHPBN2(ERA_D_T_FMT);
PHPBN2(ERA_D_FMT);
PHPBN2(ERA_T_FMT);
PHPBN2(ALT_DIGITS);
PHPBN2(INT_CURR_SYMBOL);
PHPBN2(CURRENCY_SYMBOL);
PHPBN2(CRNCYSTR);
PHPBN2(MON_DECIMAL_POINT);
PHPBN2(MON_THOUSANDS_SEP);
PHPBN2(MON_GROUPING);
PHPBN2(POSITIVE_SIGN);
PHPBN2(NEGATIVE_SIGN);
PHPBN2(INT_FRAC_DIGITS);
PHPBN2(FRAC_DIGITS);
PHPBN2(P_CS_PRECEDES);
PHPBN2(P_SEP_BY_SPACE);
PHPBN2(N_CS_PRECEDES);
PHPBN2(N_SEP_BY_SPACE);
PHPBN2(P_SIGN_POSN);
PHPBN2(N_SIGN_POSN);
PHPBN2(DECIMAL_POINT);
PHPBN2(RADIXCHAR);
PHPBN2(THOUSANDS_SEP);
PHPBN2(THOUSEP);
PHPBN2(GROUPING);
PHPBN2(YESEXPR);
PHPBN2(NOEXPR);
PHPBN2(YESSTR);
PHPBN2(NOSTR);
PHPBN2(CODESET);
PHPBN2(LOG_EMERG);
PHPBN2(LOG_ALERT);
PHPBN2(LOG_CRIT);
PHPBN2(LOG_ERR);
PHPBN2(LOG_WARNING);
PHPBN2(LOG_NOTICE);
PHPBN2(LOG_INFO);
PHPBN2(LOG_DEBUG);
PHPBN2(LOG_KERN);
PHPBN2(LOG_USER);
PHPBN2(LOG_MAIL);
PHPBN2(LOG_DAEMON);
PHPBN2(LOG_AUTH);
PHPBN2(LOG_SYSLOG);
PHPBN2(LOG_LPR);
PHPBN2(LOG_NEWS);
PHPBN2(LOG_UUCP);
PHPBN2(LOG_CRON);
PHPBN2(LOG_AUTHPRIV);
PHPBN2(LOG_LOCAL0);
PHPBN2(LOG_LOCAL1);
PHPBN2(LOG_LOCAL2);
PHPBN2(LOG_LOCAL3);
PHPBN2(LOG_LOCAL4);
PHPBN2(LOG_LOCAL5);
PHPBN2(LOG_LOCAL6);
PHPBN2(LOG_LOCAL7);
PHPBN2(LOG_PID);
PHPBN2(LOG_CONS);
PHPBN2(LOG_ODELAY);
PHPBN2(LOG_NDELAY);
PHPBN2(LOG_NOWAIT);
PHPBN2(LOG_PERROR);

/* Added in PHP5 */
PHPBN2(E_STRICT);
PHPBN2(__COMPILER_HALT_OFFSET__);

/* Class names reserved by PHP */
PHPCN(stdClass);
PHPCN(__PHP_Incomplete_Class);
PHPCN(Directory);

/* Added in PHP5 (this list apparently depends which extensions you load by default). */
PHPCN(parent);
PHPCN(self);
PHPCN(Exception);
PHPCN(php_user_filter);
PHPCN(ErrorException);
PHPCN(XMLWriter);
PHPCN(LibXMLError);
PHPCN(SimpleXMLElement);
PHPCN(SoapClient);
PHPCN(SoapVar);
PHPCN(SoapServer);
PHPCN(SoapFault);
PHPCN(SoapParam);
PHPCN(SoapHeader);
PHPCN(RecursiveIteratorIterator);
PHPCN(FilterIterator);
PHPCN(RecursiveFilterIterator);
PHPCN(ParentIterator);
PHPCN(LimitIterator);
PHPCN(CachingIterator);
PHPCN(RecursiveCachingIterator);
PHPCN(IteratorIterator);
PHPCN(NoRewindIterator);
PHPCN(AppendIterator);
PHPCN(InfiniteIterator);
PHPCN(EmptyIterator);
PHPCN(ArrayObject);
PHPCN(ArrayIterator);
PHPCN(RecursiveArrayIterator);
PHPCN(SplFileInfo);
PHPCN(DirectoryIterator);
PHPCN(RecursiveDirectoryIterator);
PHPCN(SplFileObject);
PHPCN(SplTempFileObject);
PHPCN(SimpleXMLIterator);
PHPCN(LogicException);
PHPCN(BadFunctionCallException);
PHPCN(BadMethodCallException);
PHPCN(DomainException);
PHPCN(InvalidArgumentException);
PHPCN(LengthException);
PHPCN(OutOfRangeException);
PHPCN(RuntimeException);
PHPCN(OutOfBoundsException);
PHPCN(OverflowException);
PHPCN(RangeException);
PHPCN(UnderflowException);
PHPCN(UnexpectedValueException);
PHPCN(SplObjectStorage);
PHPCN(ReflectionException);
PHPCN(Reflection);
PHPCN(ReflectionFunction);
PHPCN(ReflectionParameter);
PHPCN(ReflectionMethod);
PHPCN(ReflectionClass);
PHPCN(ReflectionObject);
PHPCN(ReflectionProperty);
PHPCN(ReflectionExtension);
PHPCN(DOMException);
PHPCN(DOMStringList);
PHPCN(DOMNameList);
PHPCN(DOMImplementationList);
PHPCN(DOMImplementationSource);
PHPCN(DOMImplementation);
PHPCN(DOMNode);
PHPCN(DOMNameSpaceNode);
PHPCN(DOMDocumentFragment);
PHPCN(DOMDocument);
PHPCN(DOMNodeList);
PHPCN(DOMNamedNodeMap);
PHPCN(DOMCharacterData);
PHPCN(DOMAttr);
PHPCN(DOMElement);
PHPCN(DOMText);
PHPCN(DOMComment);
PHPCN(DOMTypeinfo);
PHPCN(DOMUserDataHandler);
PHPCN(DOMDomError);
PHPCN(DOMErrorHandler);
PHPCN(DOMLocator);
PHPCN(DOMConfiguration);
PHPCN(DOMCdataSection);
PHPCN(DOMDocumentType);
PHPCN(DOMNotation);
PHPCN(DOMEntity);
PHPCN(DOMEntityReference);
PHPCN(DOMProcessingInstruction);
PHPCN(DOMStringExtend);
PHPCN(DOMXPath);
PHPCN(XMLReader);
PHPCN(SQLiteDatabase);
PHPCN(SQLiteResult);
PHPCN(SQLiteUnbuffered);
PHPCN(SQLiteException);

#undef PHPKW
#undef PHPBN1
#undef PHPBN2
#undef PHPCN
