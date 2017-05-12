#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
####################################
#
# Encryption/Decryption module
#
####################################
'''

import logging
import io
import os
import asyncio
import asyncio.subprocess
import hashlib

from Cryptodome.PublicKey import RSA
from Cryptodome.Random import get_random_bytes
from Cryptodome.Cipher import AES, PKCS1_OAEP

from .conf import CONF
#from .utils import cache_var

HASH_ALGORITHMS = {
    'md5': hashlib.md5,
    'sha256': hashlib.sha256,
}

LOG = logging.getLogger('crypto')

#@cache_var('MASTER_PUB_KEY')
def _master_pub_key():
    '''Fetch the RSA master public key from file'''
    keyfile = CONF.get('worker','master_pub_key')
    LOG.debug(f"Fetching the RSA master key from {keyfile}")
    with open( keyfile, 'rb') as key:
        return RSA.import_key(key_h.read(),
                              passphrase = CONF.get('worker','master_key_passphrase'))

#@cache_var('MASTER_KEY')
def _master_key():
    '''Fetch the RSA master public key from file'''
    keyfile = CONF.get('worker','master_key')
    LOG.debug(f"Fetching the RSA master key from {keyfile}")
    with open( keyfile, 'rb') as key_h:
        return RSA.import_key(key_h.read(),
                              passphrase = CONF.get('worker','master_key_passphrase'))

def make_header(enc_key_size, nonce_size, aes_mode, chunk_size):
    '''Create the header line for the re-encrypted files

    The header is simply of the form:
    Encryption key size (in bytes) | Nonce size | AES mode | Chunk size
    '''
    header = f'{enc_key_size}|{nonce_size}|{aes_mode}|{chunk_size}\n'
    return header.encode('utf-8')

def from_header(h):
    '''Convert the given line into differents values, doing the opposite job as `make_header`'''
    header = bytearray()
    while True:
        b = h.read(1)
        if b in (b'\n', b''):
            break
        header.extend(b)

    LOG.debug(f'Found header: {header!r}')
    enc_key_size, nonce_size, aes_mode, chunk_size, *rest = header.split(b'|')
    assert( not rest )
    return (int(enc_key_size),int(nonce_size), aes_mode.decode(), int(chunk_size))

def encrypt_engine():
    '''Generator that takes a block of data as input and encrypts it as output.

    The encryption algorithm is AES (in CTR mode), using a randomly-created session key.
    The session key is encrypted with RSA.
    '''

    LOG.info('Starting the cipher engine')
    session_key = get_random_bytes(32) # for AES-256
    LOG.debug(f'session key    = {session_key}')

    LOG.info('Creating AES cypher (CTR mode)')
    aes = AES.new(key=session_key, mode=AES.MODE_CTR)

    LOG.info('Creating RSA cypher')
    rsa = PKCS1_OAEP.new(_master_key())

    encryption_key = rsa.encrypt(session_key)
    LOG.debug(f'\tencryption key = {encryption_key}')

    nonce = aes.nonce
    LOG.debug(f'AES nonce: {nonce}')

    clearchunk = yield (encryption_key, 'CTR', nonce)

    while True:
        clearchunk = yield aes.encrypt(clearchunk)
        # if clearchunk is None:
        #     LOG.info('Exiting the encryption engine')
        #     break # exit the generator

class ReEncryptor(asyncio.SubprocessProtocol):
    '''Re-encryption protocol.

    Each block of data received from the pipe is added to a buffer.
    When the buffer grows over a certain size `s`, the `s` first bytes of the buffer are re-encrypted using RSA/AES.

    We also calculate the checksum of the data received in the pipe.
    '''

    def __init__(self, hashAlgo, target_h, done):
        self.done = done
        self._buffer = bytearray()
        engine = encrypt_engine()
        self.chunk_size = CONF.getint('worker','random_access_chunk_size',fallback=1 << 26) # 67 MB or 2**26
        self.target_handler = target_h

        try:
            h = HASH_ALGORITHMS.get(hashAlgo)
        except KeyError:
            raise ValueError('No support for the secure hashing algorithm')
        else:
            self.digest = h()
            self.target_digest = hashlib.sha256()

        encryption_key, mode, nonce = next(engine)
        self.header = make_header(len(encryption_key), len(nonce), mode, self.chunk_size)
        LOG.info(f'Writing header to file: {self.header[:-1]}')
        self.target_handler.write(self.header) # includes \n
        self.target_digest.update(self.header)
        LOG.debug('Writing key to file')
        self.target_handler.write(encryption_key)
        self.target_digest.update(encryption_key)
        LOG.debug('Writing nonce to file')
        self.target_handler.write(nonce)
        self.target_digest.update(nonce)
        self.engine = engine

    def pipe_data_received(self, fd, data):
        # Data is of size: 32768 bytes
        if not data:
            return
        if fd == 1:
            self._buffer.extend(data)
            self.digest.update(data)
            while True:
                if len(self._buffer) < self.chunk_size:
                    break
                data = self._buffer[:self.chunk_size]
                self._process_chunk(data)
                self._buffer = self._buffer[self.chunk_size:]
        else:
            LOG.debug(f'ignoring data on fd {fd}: {data}')

    def process_exited(self):
        if len(self._buffer) > 0:
            self._process_chunk(self._buffer)
        self._buffer = bytearray()
        # LOG.info('Closing the encryption engine')
        # self.engine.send(None) # closing it
        self.done.set_result(self.digest.hexdigest())

    def _process_chunk(self,data):
        assert len(data) <= self.chunk_size, "Chunk too large"
        LOG.debug('processing {} bytes of data'.format(len(data)))
        data = bytes(data) # Not good!
        cipherchunk = self.engine.send(data)
        self.target_handler.write(cipherchunk)
        self.target_digest.update(cipherchunk)


def ingest(enc_file,
           org_hash,
           hash_algo,
           target
):
    '''Decrypts a gpg-encoded file and verifies the integrity of its content.
       Finally, it re-encrypts it chunk-by-chunk'''

    assert( isinstance(org_hash,str) )

    #return ('File: {} and {}: {}'.format(filepath, hashAlgo, filehash))
    LOG.debug(f'Processing file\n'
              f'==============\n'
              f'enc_file  = {enc_file}\n'
              f'org_hash  = {org_hash}\n'
              f'hash_algo = {hash_algo}\n'
              f'target    = {target}')

    code = [ CONF.get('worker','gpg_exec'),
             '--homedir', CONF.get('worker','gpg_home'),
             '--decrypt', enc_file
    ]

    LOG.debug(f'Prepare Decryption with {code}')

    _errmsg = None

    with open(target, 'wb') as target_h:

        loop = asyncio.get_event_loop()
        done = asyncio.Future(loop=loop)
        reencrypt_protocol = ReEncryptor(hash_algo, target_h, done)

        async def _re_encrypt():
            gpg_job = loop.subprocess_exec(lambda: reencrypt_protocol, *code,
                                           stdin=None,
                                           stdout=asyncio.subprocess.PIPE,
                                           stderr=asyncio.subprocess.DEVNULL # suppressing progress messages
            )
            transport, _ = await gpg_job
            await done
            gpg_retcode = transport.get_returncode()
            transport.close()
            return (gpg_retcode, done.result())

        gpg_result, calculated_digest = loop.run_until_complete(_re_encrypt())

        LOG.debug(f'Calculated digest: {calculated_digest}')
        LOG.debug(f'Compared to digest: {org_hash}')
        correct_digest = (calculated_digest == org_hash)

        if not correct_digest:
            _errmsg = f'Invalid {hash_algo} checksum for decrypted content of {enc_file}'
        if gpg_result != 0: # Swapped order on purpose
            _errmsg = f'Error decrypting the file'


    if _errmsg:
        LOG.error(f'{_errmsg!r}')
        LOG.warning(f'Removing {target}')
        os.remove(target)
        raise Exception(_errmsg)
    else:
        LOG.info(f'File encrypted')
        return (reencrypt_protocol.header, # returning the header for that file
                reencrypt_protocol.target_digest.hexdigest(),
                CONF.get('worker','master_key'))  # That was the key used at that moment

def chunker(stream, chunk_size=None):
    """Lazy function (generator) to read a stream one chunk at a time."""

    if not chunk_size:
        chunk_size = CONF.getint('worker','random_access_chunk_size',fallback=1 << 26) # 67 MB or 2**26

    assert(chunk_size >= 16)
    #assert(chunk_size % 16 == 0)
    LOG.debug(f'\tchunk size = {chunk_size}')
    yield chunk_size
    while True:
        data = stream.read(chunk_size)
        if not data:
            return None # No more data
        yield data

def decrypt_engine(encrypted_session_key, aes_mode, nonce):

    LOG.info('Starting the decipher engine')

    LOG.info('Creating RSA cypher')
    rsa = PKCS1_OAEP.new(_master_key())
    session_key = rsa.decrypt(encrypted_session_key)

    LOG.info(f'Creating AES cypher in mode {aes_mode}')
    aes = AES.new(key=session_key, mode=getattr(AES, 'MODE_' + aes_mode), nonce=nonce)

    LOG.info(f'Session key: {session_key}')
    LOG.info(f'Nonce: {nonce}')

    cipherchunk = yield

    while True:
        cipherchunk = yield aes.decrypt(cipherchunk)


def decrypt_from_vault( source_h, target_h ):

    LOG.debug('Decrypting file')
    enc_key_size, nonce_size, aes_mode, chunk_size = from_header( source_h )

    LOG.debug(f'encrypted_session_key (size): {enc_key_size}')
    LOG.debug(f'aes mode: {aes_mode}')
    LOG.debug(f'chunk size: {chunk_size}')

    encrypted_session_key = source_h.read(enc_key_size)
    nonce = source_h.read(nonce_size)

    engine = decrypt_engine( encrypted_session_key, aes_mode=aes_mode.upper(), nonce=nonce )
    next(engine) # start it

    chunks = chunker(source_h, # the rest
                     chunk_size)
    next(chunks) # start it and ignore its return value

    for chunk in chunks:
        clearchunk = engine.send(chunk)
        target_h.write(clearchunk)


